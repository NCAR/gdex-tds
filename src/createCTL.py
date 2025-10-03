#!/usr/bin/env python
"""
Creating the .ctl entries about TDS links for a given dataset

Usage:
    createCTL.py [dsid]

Example:
    createCTL.py d010077
"""

import sys
import os
import psycopg2 as sql
from dotenv import load_dotenv, find_dotenv
# import xml.etree.ElementTree as ET
# import pdb
# import yaml

# Load environment variables from .env file (searches up directory tree)
load_dotenv(find_dotenv())


def usage():
    """Print usage information for the script."""
    sys.stderr.write('Usage:\n')
    sys.stderr.write('    ' + sys.argv[0] + ' [dsid] \n')
    exit(1)

def get_dsid():
    """get dsid arg, check if valid and fix if possible."""
    # check the arguments are provided
    if len(sys.argv) <= 1:
        usage()

    # store dsid arg
    ds_id = sys.argv[1]

    # check if dsid is valid in the format of dxxxxxx
    ## check if it starts with d, if not add it
    if not ds_id.startswith('d'):
        ds_id = 'd' + ds_id
    ## check if the rest is an integer and 6 digits long
    if len(ds_id) != 7:
        sys.stderr.write('Error: [dsid] must be in the format of dxxxxxx (dxxxxxx/xxxxxx).\n')
        exit(1)
    if not ds_id[1:].isdigit():
        sys.stderr.write('Error: [dsid] must be an integer (dxxxxxx/xxxxxx).\n')
        exit(1)
    return ds_id

def write_seperator():
    """Write '<:>' to stdout"""
    sys.stdout.write('<:>')

def create_ctl_entry(
    ds_id:str,
    specialist:str,
    # access_type:str,
    dirname:str="",
    gindex:int=None
):
    """
    Create a .ctl entry for the given dsid,
    specialist, access_type, dirname, and gindex.

    Control file format:
    ControlIndex<:>Dataset<:>GroupIndex<:>RequestType<:>ControlMode<:>TarFlag<:>Specialist<:>ProcessCommand<:>EmptyOutput<:>URL<:>HostName<:>
    1317<:>ds633.0<:>38<:>N<:>A<:>N<:>davestep<:><:>N<:>https://rda.ucar.edu/thredds/catalog/files/e/ds633.0/e5.oper.fc.sfc.minmax/catalog.html<:><:>
    ....

    Parameters
    ----------
    ds_id : str
        The dataset ID (e.g., 'd010077').
    specialist : str
        The specialist associated with the dataset.
    access_type : str (currently not used in the function, commented out in parameters)
        The access type ('g' for general, 'p' for private).
    dirname : str, optional
        The directory name within the dataset (default is "").
    gindex : int or None, optional
        The group index (default is None, represent group index = 0).

    """

    if len(dirname) > 0 and dirname[-1] != '/':
        dirname += '/'
    dirname += "catalog.html"


    sys.stdout.write('0') # Write index = 0 because index is not yet defined
    write_seperator()
    sys.stdout.write(ds_id)
    write_seperator()
    if gindex is None:
        sys.stdout.write('0') # Write 0 when refering to all products
    else:
        sys.stdout.write(str(gindex))
    write_seperator()
    sys.stdout.write('N')
    write_seperator()
    sys.stdout.write('A')
    write_seperator()
    sys.stdout.write('N')
    write_seperator()
    sys.stdout.write(specialist)
    write_seperator()
    write_seperator()
    sys.stdout.write('N')
    write_seperator()
    sys.stdout.write('https://tds.gdex.ucar.edu/thredds/catalog/files/'+ds_id+'/'+dirname)
    write_seperator()
    write_seperator()
    sys.stdout.write('\n')

if __name__ == "__main__":

    # get dataset ID and dssdb password for access rdadb
    dsid = get_dsid()

    # Get password from environment variable or prompt the user
    pw = os.getenv('DB_PASSWORD')
    if pw is None:
        pw = input("Enter db pw: ")

    ## New Connection to dssdb
    conn = sql.connect(user = 'dssdb', password=pw, host = 'rda-db.ucar.edu', database='rdadb')
    cursor = conn.cursor()

    # Get Specialist
    query = f"select specialist from dsowner where dsid='{dsid}';"
    cursor.execute(query)
    specialist1, = cursor.fetchall()[0]

    # # Get Access rights (currently not used in the function, commented out in parameters)
    # query = f"select access_type from dataset where dsid='{dsid}';"
    # cursor.execute(query)
    # rights, = cursor.fetchall()[0]
    # if rights is not None:
    #     access_type1 = rights
    # else:
    #     access_type1 = 'g'

    query = f"select grpid,gindex from dsgroup where dsid='{dsid}' and pindex=0;"
    cursor.execute(query)
    #grpid,gindex = cursor.fetchall()
    all_ents = cursor.fetchall()

    # create the top level catalog entry for the whole dataset
    # create_ctl_entry(dsid, specialist1, access_type1) # Create group 0
    create_ctl_entry(dsid, specialist1) # Create group 0

    # create entries for each group that is under the subdirectory of the dataset
    for grpid1,gindex1 in all_ents:
        # create_ctl_entry(dsid, specialist1, access_type1, grpid, gindex1)  # Create group 0
        create_ctl_entry(dsid, specialist1, grpid1, gindex1)



