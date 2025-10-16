"""
A Prefect flow to add new datasets to the THREDDS Data Server (TDS) catalog.

The flow performs the following steps:
1. Retrieves all dataset IDs from the metadata database.
2. Retrieves all dataset IDs currently listed in the TDS catalog XML file.
3. For each dataset ID in the database:
   a. If it is already in the catalog, skip it.
   b. Check if its format is supported by TDS (netcdf, grib1, grib2).
   c. If supported:
      - Create XML for the dataset using an existing script.
      - Add it to the catalog in alphabetical order by title.

Environment variables loaded from local .env file
"""


import os
import sys
import subprocess
from datetime import datetime
import psycopg2 as sql
from prefect import flow, task
from prefect.logging import get_run_logger
import xml.etree.ElementTree as ET

# Get the directory of this script and the project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Project root directory

# for reading local .env file
try:
    # Load environment variables from .env file (searches up directory tree)
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    sys.exit("databased pw not set in env")

#### prefect pydantic warning suppress ####
# Set environment variable to suppress warnings globally
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:pydantic._internal._generate_schema'
##########################################



@task
def get_all_db_dsid():
    """Get all dataset IDs from the database.
    
    Returns
    -------
    list
        List of all dataset IDs from the database.
    """
    # Get password from environment variable or prompt the user
    pw = os.getenv('META')
    if pw is None:
        pw = input("Enter metadata pw: ")

    # New Connection to search db
    conn = sql.connect(user='metadata', password=pw, host='rda-db.ucar.edu', database='rdadb')
    cursor = conn.cursor()

    # Query all dataset IDs
    query = "select dsid from search.datasets order by dsid"
    cursor.execute(query)
    dataset_ids = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return dataset_ids

@task
def get_all_tds_dsid(catalog_file: str):
    """Get all dataset IDs from the TDS catalog XML file.
    
    Parameters
    ----------
    catalog_file : str
        Path to the catalog.xml file.
    
    Returns
    -------
    list
        List of dataset IDs extracted from the catalogRef elements.
    """
    tree = ET.parse(catalog_file)
    root = tree.getroot()

    xmlns = 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0'
    xmlns_xlink = 'http://www.w3.org/1999/xlink'

    # Define namespace map for finding elements
    namespaces = {
        'thredds': xmlns,
        'xlink': xmlns_xlink
    }

    # Collect all existing catalogRef elements - default namespace
    # not showing up in findall without prefix
    # using the 'thredds' prefix defined in namespaces
    catalog_refs = list(root.findall('thredds:catalogRef', namespaces))

    # Extract dataset IDs from xlink:href attributes
    dataset_ids = []
    for ref in catalog_refs:
        href = ref.get('{'+xmlns_xlink+'}href', '')
        if href.startswith('catalog_') and href.endswith('.xml'):
            dsid = href[len('catalog_'):-len('.xml')]
            dataset_ids.append(dsid)

    return dataset_ids

@task
def check_format(dataset_id: str) -> bool:
    """Check if format is supported by TDS.
    currently supported formats: netcdf, grib1, grib2

    Parameters
    ----------
    dataset_id : str
        The dataset ID to check.
    
    Returns
    -------
    bool
        True if format is supported by TDS, False otherwise.
    """
    # Get password from environment variable or prompt the user
    pw = os.getenv('META')
    if pw is None:
        pw = input("Enter metadata pw: ")

    # New Connection to search db
    conn = sql.connect(user = 'metadata', password=pw, host = 'rda-db.ucar.edu', database='rdadb')
    cursor = conn.cursor()

    # Get format
    query = "select keyword from search.formats where dsid='"+dataset_id+"'"
    cursor.execute(query)
    all_rows = cursor.fetchall()
    data_formats = [row[0].lower() for row in all_rows]

    cursor.close()
    conn.close()

    # currently supported formats
    supported_formats = ['netcdf', 'grib1', 'grib2']
    for data_format in data_formats:
        for supported in supported_formats:
            if supported in data_format:
                return True
    return False

@task
def create_xml(dataset_id: str):
    """Create XML for the dataset using the existing script.
    Parameters
    ----------
    dataset_id : str
        The dataset ID to create XML for. 
        Currently set output directory to rda-tds/content/

    Returns
    -------
    None
    """

    try:
        subprocess.run([
            os.path.join(PROJECT_ROOT, "src/createXML.py"),
            dataset_id,
            os.path.join(PROJECT_ROOT, "rda-tds/content/")
        ], check=True)
        err_msg = ""
        return True, err_msg
    except subprocess.CalledProcessError as e:
        if e.returncode == 250:
            err_msg = f"dataset {dataset_id}: has different datatypes, skipping"
            return False, err_msg
        else:
            raise

@task
def add_catalog_ref_sorted(catalog_file: str, new_dsid: str, new_title: str):
    """
    Add a new catalogRef to the catalog while maintaining alphabetical order by title.
    
    Parameters
    ----------
    catalog_file : str
        Path to the catalog XML file.
    new_dsid : str
        The dataset ID for the new catalogRef.
    new_title : str
        The title for the new catalogRef.
    
    Returns
    -------
    None

    Usage
    -----
    add_catalog_ref_sorted(
        'rda-tds/content/catalog.xml',
        'd123456',
        'Example New Dataset Title for Testing'
    )
    """
    # Register namespaces
    ET.register_namespace('', 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

    # Parse the XML
    tree = ET.parse(catalog_file)
    root = tree.getroot()

    xmlns = 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0'
    xmlns_xlink = 'http://www.w3.org/1999/xlink'

    # Define namespace map for finding elements
    namespaces = {
        'thredds': xmlns,
        'xlink': xmlns_xlink
    }

    # Create the new catalogRef element
    new_ref = ET.Element('catalogRef')
    new_ref.set('{'+xmlns_xlink+'}href', f'catalog_{new_dsid}.xml')
    new_ref.set('{'+xmlns_xlink+'}title', f'{new_dsid} {new_title}')
    new_ref.set('name', '')
    new_ref.tail = '\n    ' #indentation and newline for pretty print

    # Collect all existing catalogRef elements - default namespace
    # not showing up in findall without prefix
    # using the 'thredds' prefix defined in namespaces
    catalog_refs = list(root.findall('thredds:catalogRef', namespaces))

    # Add the new element to the list
    catalog_refs.append(new_ref)

    # Sort by xlink:title attribute (case-insensitive)
    def get_title(elem):
        title = elem.get('{'+xmlns_xlink+'}title', '')
        return title.lower()

    catalog_refs.sort(key=get_title)

    # Remove all existing catalogRef elements from root
    for ref in list(root):
        if ref.tag == '{'+xmlns+'}catalogRef':
            root.remove(ref)

    # Add sorted catalogRef elements back to root
    for ref in catalog_refs:
        root.append(ref)

    # Write the updated XML back to file
    tree.write(catalog_file, encoding='utf-8', xml_declaration=True)
    # print(f"Added {new_dsid} to catalog in sorted position")


@task
def add2catalog(dataset_id: str):
    """Add the dataset to the catalog.xml file in sorted order.

    Utilizes `add_catalog_ref_sorted` to maintain alphabetical order by title.
    
    Parameters
    ----------
    dataset_id : str
        The dataset ID to add to the catalog.
    
    Returns
    -------
    None

    """

    # Get password from environment variable or prompt the user
    pw = os.getenv('META')
    if pw is None:
        pw = input("Enter metadata pw: ")

    # New Connection to search db
    conn = sql.connect(user = 'metadata', password=pw, host = 'rda-db.ucar.edu', database='rdadb')
    cursor = conn.cursor()

    # Get title
    query = "select title from search.datasets where dsid='"+dataset_id+"'"
    cursor.execute(query)
    title, = cursor.fetchall()[0]

    cursor.close()
    conn.close()

    # Add title and catalogRef to catalog.xml
    catalog_file = os.path.join(
        PROJECT_ROOT,
        'rda-tds/content/catalog.xml'
    )
    add_catalog_ref_sorted(
        catalog_file,
        dataset_id,
        title
    )

@flow(timeout_seconds=60*10,log_prints=True)
def add_data2tds():
    """The main prefect flow to add new dataset to TDS.
    Steps:
    1. Get all dataset IDs from the database.
    2. Get all dataset IDs from the catalog.xml file.
    3. For each dataset ID in the database:
       a. If it is already in the catalog, skip it.
       b. Check if its format is supported by TDS.
       c. If supported
            - create XML for the dataset
            - add it to the catalog.
    """
    # set up logger from prefect
    logger = get_run_logger()

    # Get all dataset IDs in the database
    all_dsids = get_all_db_dsid()
    logger_info = f"Total datasets in database: {len(all_dsids)}"
    logger.info(logger_info)

    # Get all dataset IDs in the catalog (tds datasets are based on catalogRef entries)
    catalog_file = os.path.join(
        PROJECT_ROOT,
        'rda-tds/content/catalog.xml'
    )
    tds_dsids = get_all_tds_dsid(catalog_file)
    logger_info = f"Total datasets in TDS: {len(tds_dsids)}"
    logger.info(logger_info)

    # loop over dataset IDs in the database
    new_datasets_add = []
    for dsid in all_dsids:
        if dsid in tds_dsids:
            logger_warning = f"Skipping {dsid}: already in catalog"
            logger.warning(logger_warning)
            continue

        # check if format is supported by TDS
        tds_compatible = check_format(dsid)

        if not tds_compatible:
            logger_warning = f"Skipping {dsid}: format not supported by TDS"
            logger.warning(logger_warning)
            continue


        # check if individual dataset XML exist
        # if exist skip and log error
        data_xml = os.path.join(PROJECT_ROOT, 'rda-tds/content/', f'catalog_{dsid}.xml')
        if os.path.exists(data_xml):
            logger_error = f"Skipping {dsid}: individual XML already exists but not in catalog. Need to do manual check!!!"
            logger.error(logger_error)
            continue

        logger_info = f"Adding {dsid} to TDS"
        logger.info(logger_info)
        # store data id for data logging
        new_datasets_add.append(dsid)

        # create XML for the dataset
        state, err = create_xml(dsid)

        if not state:
            logger_error = f"Failed to create XML for {dsid}: {err}"
            logger.error(logger_error)
            continue

        # add to catalog.xml
        add2catalog(dsid)

    # final log of new datasets added to TDS
    if new_datasets_add:
        data_log = os.path.join(PROJECT_ROOT, 'prefect-workflow/new_datasets_added.log')
        with open(data_log, 'a', encoding='utf-8') as log_file:
            for new_dsid in new_datasets_add:
                date_data_info = datetime.now().strftime("%Y-%m-%d-%H%M%S")
                log_file.write(f"[{date_data_info}] - {new_dsid} added\n")

if __name__ == "__main__":

    # run the main flow
    add_data2tds()
