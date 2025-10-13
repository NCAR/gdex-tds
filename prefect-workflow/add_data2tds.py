import os
import sys
import subprocess
import psycopg2 as sql
from prefect import flow, task
import xml.etree.ElementTree as ET

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
    pw = os.getenv('META_PASSWORD')
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
        Path to the catalog XML file.
    
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
    """
    # Get password from environment variable or prompt the user
    pw = os.getenv('META_PASSWORD')
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
    subprocess.run(["src/createXML.py", dataset_id, "rda-tds/content/"], check=True)

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
def add_to_catalog(dataset_id: str):

    # Get password from environment variable or prompt the user
    pw = os.getenv('META_PASSWORD')
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
    add_catalog_ref_sorted('rda-tds/content/catalog.xml', dataset_id, title)

@flow(log_prints=True)
def add_data2tds():

    # Get all dataset IDs in the database
    all_dsids = get_all_db_dsid()

    # Get all dataset IDs in the catalog (tds datasets are based on catalogRef entries)
    tds_dsids = get_all_tds_dsid('rda-tds/content/catalog.xml')

    # loop over dataset IDs in the database
    for dsid in all_dsids:
        if dsid in tds_dsids:
            print(f"Skipping {dsid}: already in catalog")
            continue
        
        # check if format is supported by TDS
        tds_compatible = check_format(dsid)

        if not tds_compatible:
            print(f"Skipping {dsid}: format not supported by TDS")
            continue

        print(f"Skipping {dsid}: already in catalog")
        # create XML for the dataset
        create_xml(dsid)

        # add to catalog
        add_to_catalog(dsid)

if __name__ == "__main__":
    add_data2tds()
