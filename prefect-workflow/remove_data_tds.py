"""
A Prefect flow to remove datasets from the THREDDS Data Server (TDS) catalog.

The flow performs the following steps:
1. Retrieves all dataset IDs currently listed in the TDS catalog XML file.
2. For each dataset ID listed in the exclude_data.json file:
   a. If it is in the catalog, remove its catalogRef entry.
   b. Delete the corresponding individual dataset XML file if it exists.
   c. Log the removal action with a timestamp.

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
from auto_add_data_tds import get_all_tds_dsid

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
def remove_catalog_ref_sorted(catalog_file: str, remove_dsids: list[str]):
    """
    Remove a catalogRef from the catalog while maintaining alphabetical order by title.

    Parameters
    ----------
    catalog_file : str
        Path to the catalog XML file.
    remove_dsid : str
        The dataset ID to remove from the catalog.
    
    Returns
    -------
    None

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

    # Collect all existing catalogRef elements - default namespace
    # not showing up in findall without prefix
    # using the 'thredds' prefix defined in namespaces
    catalog_refs = list(root.findall('thredds:catalogRef', namespaces))


    # Remove catalogRef  with title including remove_dsids elements from root
    # TODO: optimize needed to avoid nested loop
    for remove_dsid in remove_dsids:
        for ref in list(root):
            href_value = f"catalog_{remove_dsid}.xml"
            cond1 = (ref.tag == '{'+xmlns+'}catalogRef')
            cond2 = (ref.attrib.get('{http://www.w3.org/1999/xlink}href') == href_value)
            if cond1 and cond2:
                root.remove(ref)

    # Write the updated XML back to file
    tree.write(catalog_file, encoding='utf-8', xml_declaration=True)
    # print(f"Added {new_dsid} to catalog in sorted position")

@flow(timeout_seconds=60*10,log_prints=True)
def remove_data():
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
