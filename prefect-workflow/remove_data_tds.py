"""
A Prefect flow to remove datasets from the THREDDS Data Server (TDS) catalog.

The flow performs the following steps:
1. Retrieves all dataset IDs currently listed in the TDS catalog XML file.
2. For each dataset ID listed in the remove_data_tds.json file:
   a. If it is in the catalog, remove its catalogRef entry.
   b. Delete the corresponding individual dataset XML file if it exists.
   c. Log the removal action with a timestamp.

Environment variables loaded from local .env file
"""


import os
import sys
import json
from datetime import datetime
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

    # Collect all existing catalogRef elements - 
    # default namespace not showing up in findall without prefix
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
    """The main prefect flow to remove dataset from TDS.
    """
    # set up logger from prefect
    logger = get_run_logger()

    # read the json file for dataset IDs to remove
    json_file = os.path.join(SCRIPT_DIR, 'remove_data_tds.json')
    with open(json_file, 'r', encoding='utf-8') as jf:
        json_data = json.load(jf)
    all_remove_dsids = json_data.get('remove_data', [])
    if not all_remove_dsids:
        logger.info("No dataset IDs to remove. Exiting flow.")
        return

    # Get the catalog (tds datasets are based on catalogRef entries)
    main_catalog_file = os.path.join(
        PROJECT_ROOT,
        'rda-tds/content/catalog.xml'
    )

    # remove data in catalog.xml
    remove_catalog_ref_sorted(main_catalog_file, all_remove_dsids)

    # remove individual dataset XML files
    for dsid in all_remove_dsids:
        data_xml = os.path.join(PROJECT_ROOT, 'rda-tds/content/', f'catalog_{dsid}.xml')
        if os.path.exists(data_xml):
            os.remove(data_xml)
            logger.info(f"Removed individual dataset XML file for {dsid}")


    # final log of new datasets added to TDS
    date_data_info = datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
    if all_remove_dsids:
        data_log = os.path.join(PROJECT_ROOT, f'prefect-workflow/remove_data_tds_{date_data_info}.log')
        with open(data_log, 'a', encoding='utf-8') as log_file:
            for dsid in all_remove_dsids:
                log_file.write(f"[{date_data_info}] - {dsid} removed\n")

if __name__ == "__main__":

    # run the main flow
    remove_data()
