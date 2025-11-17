"""
The script adds the TDS URL entry on the dataset page
through adding the control index in the database

To be able to run this script, one need to first generate
the "auto_add_data_tds_{datetime}.log" file through
running the "generate_auto_add_data_tds.py" script.

Steps:
1. The new added index is generated from 
```
python src/createCTL.py <dsid>
```

2. Generate the original control file through
```
dsrqst -gc -ds <dsid>
```

3. The script will parse the log file to get the list of dataset IDs
to add the TDS URL entry through 
```
dsrqst -sc -ds <dsid> -if <control_file> -md -nc
```
"""
import os
import requests
import subprocess


# setup log file name to be read
LOG_FILE_NAME = "auto_add_data_tds_2025-11-14-12_31_54.log"

# Get the directory of this script and the project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Project root directory


def url_is_ok(url):
    """
    Check if a URL is reachable (status code 200-399).

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    bool
        True if the URL is reachable (status code 200-399), False otherwise.
    """
    try:
        response = requests.get(url, timeout=10)
        return response.ok  # True if status_code is 200-399
    except Exception as e:
        print(f"Error: {e}")
        return False

def parse_log_file(log_file: str) -> list[str]:
    """Parse the log file to get the list of dataset IDs to add TDS URL entry.

    Args:
        log_file (str): Path to the log file.

    Returns:
        list[str]: List of dataset IDs.
    """
    dsids = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            list_text = line.strip().split()
            dsid = list_text[-2].strip()
            dsids.append(dsid)
    return dsids

def get_control_file(dsid: str) -> str:
    """Generate the original control file for the given dataset ID.

    Args:
        dsid (str): Dataset ID.

    Returns:
        str: Path to the generated control file.
    """

    command = ["dsrqst", "-gc", "-ds", dsid]

    # Run the command
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        # store standard output lines
        control_info = result.stdout.strip().splitlines()
        # remove the first and last lines
        control_lines = control_info[1:-1]
        return control_lines

    except subprocess.CalledProcessError as err_result:
        print(f"Command failed with exit code {err_result.returncode}")
        print(f"STDOUT: {err_result.stdout}")
        print(f"STDERR: {err_result.stderr}")
        return err_result

def create_ctl(dataset_id: str):
    """Create CTL file for the dataset using the existing script.
    Parameters
    ----------
    dataset_id : str
        The dataset ID to create CTL for. 

    Returns
    -------
        standard output from the createCTL.py
    """
    command = ["python", os.path.join(PROJECT_ROOT,'src','createCTL.py'), dataset_id]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )

        # store standard output lines
        control_lines = result.stdout.strip().splitlines()
        return control_lines
    except subprocess.CalledProcessError as e:
        raise e

def create_control_file(dsid: str) -> str:
    """Create the new control file for the given dataset ID.
    this add the new TDS URL entry on the original control file.
    Currently set output directory to prefect-workflow/

    Parameters
    ----------
    dsid : str
        Dataset ID.
    control_lines : list[str]
        Original control file lines.

    Returns
    -------
    str
        Path to the new control file.
    """
    # use createCTL.py to generate the new control file lines
    new_control_lines = create_ctl(dsid)

    # test the new control lines for URL validity
    tested_new_control_lines = []
    for line in new_control_lines:
        infos = line.strip().split('<:>')
        url = infos[9]
        # skip the TDS url if URL not working
        if not url_is_ok(url):
            continue
        tested_new_control_lines.append(line)

    # get original control file
    old_control_lines = get_control_file(dsid)

    # combine the original control lines with the new TDS URL entry
    combined_control_lines = old_control_lines + tested_new_control_lines

    # write to new control file
    control_file_path = os.path.join(PROJECT_ROOT,'prefect-workflow',f"{dsid}_new.ctl")

    with open(control_file_path, 'w', encoding='utf-8') as f:
        for line in combined_control_lines:
            f.write(line + '\n')

    return control_file_path

def add_tds_url(dsid: str, new_control_file: str):
    """Add the TDS URL entry to the dataset page using the control file.

    Parameters
    ----------
    dsid : str
        Dataset ID.
    new_control_file : str
        Path to the new control file.
    """

    command = ["dsrqst", "-sc", "-ds", dsid, "-if", new_control_file, "-md", "-nc"]

    # Run the command
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Successfully added TDS URL for dataset {dsid}")
        print(f"STDOUT: {result.stdout}")
        return result

    except subprocess.CalledProcessError as err_result:
        print(f"Failed to add TDS URL for dataset {dsid} with exit code {err_result.returncode}")
        print(f"STDOUT: {err_result.stdout}")
        print(f"STDERR: {err_result.stderr}")
        return err_result

def main():
    """Main function to add TDS URL entries for datasets listed in the log file."""

    data_log_file = os.path.join(PROJECT_ROOT,'prefect-workflow',LOG_FILE_NAME)
    dsids = parse_log_file(data_log_file)

    for dsid in dsids:
        print(f"Processing dataset ID: {dsid}")
        # create new control file with TDS URL entry
        new_control_file = create_control_file(dsid)
        print(f"New control file created at: {new_control_file}")
        # add TDS URL entry using the new control file
        dsrqst_result = add_tds_url(dsid, new_control_file)
        if dsrqst_result.returncode == 1:
            # DO NOT remove the new control file if failed (easier to track the issue)
            log_error = f"Failed to add TDS URL for {dsid} for web access."
            print(log_error)
            continue
        log_info = f"Successfully add TDS URL for {dsid} for web access."
        print(log_info)
        # remove the new control file after processing
        os.remove(new_control_file)
        print(f"Removed temporary control file: {new_control_file}")
        print("--------------------------------------------------")

if __name__ == "__main__":
    main()
