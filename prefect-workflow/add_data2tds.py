import subprocess
import warnings
import os
from prefect import flow, task

# Set environment variable to suppress warnings globally
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:pydantic._internal._generate_schema'

# Suppress all Pydantic field attribute warnings (including internal calls)
warnings.filterwarnings("ignore", message=".*UnsupportedFieldAttributeWarning.*")
warnings.filterwarnings("ignore", message=".*The 'default' attribute with value.*was provided to the.*Field.*function.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal._generate_schema")


@task
def create_xml():
    subprocess.run(["../src/createXML.py", "d010077"], check=True)

@flow
def add_data2tds_flow():
    create_xml()

