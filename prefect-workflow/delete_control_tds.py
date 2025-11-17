"""
The script modify the TDS URL entry on the dataset page
through updating the control index in the database

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
import subprocess
from add_control_tds import get_control_file, parse_log_file, url_is_ok

# setup log file name to be read
LOG_FILE_NAME = "auto_add_data_tds_2025-11-14-12_31_54.log"

# Get the directory of this script and the project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Project root directory


def delete_breaking_control(dsid: str) -> str:
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
    # get original control file
    old_control_lines = get_control_file(dsid)

    # modify the origin control lines
    remain_control_lines = [old_control_lines[0]]
    for line in old_control_lines[1:]:
        infos = line.strip().split('<:>')
        control_index = infos[0]
        url = infos[9]

        # TDS condition
        RequestType = 'N'
        ControlMode = 'A'
        TarFlag = 'N'
        ProcessCommand = ''
        EmptyOutput = 'N'
        HostName = ''
        if (RequestType != infos[3] or
            ControlMode != infos[4] or
            TarFlag != infos[5] or
            ProcessCommand != infos[7] or
            EmptyOutput != infos[8] or
            HostName != infos[10]):
            # skip the TDS url modification
            continue

        # remove the control index if URL not working
        if not url_is_ok(url):
            delete_tds_url(dsid,control_index)
            continue

        remain_control_lines.append(line)


    # write to new control file
    control_file_path = os.path.join(PROJECT_ROOT,'prefect-workflow',f"{dsid}_remain.ctl")

    with open(control_file_path, 'w', encoding='utf-8') as f:
        for line in remain_control_lines:
            f.write(line + '\n')

    return control_file_path


def delete_tds_url(dsid: str, control_index: str):
    """Delete the TDS URL entry through dsrqst.

    Parameters
    ----------
    dsid : str
        Dataset ID.
    new_control_file : str
        Path to the new control file.
    """

    command = ["dsrqst", "-dl", "-ds", dsid, "-ci", control_index, "-md"]

    # Run the command
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Successfully deleted TDS URL for dataset {dsid} control index {control_index}")
        print(f"STDOUT: {result.stdout}")
        return result

    except subprocess.CalledProcessError as err_result:
        print(f"Failed to delete TDS URL for dataset {dsid} control index {control_index} with exit code {err_result.returncode}")
        print(f"STDOUT: {err_result.stdout}")
        print(f"STDERR: {err_result.stderr}")
        return err_result

def main():
    """Main function to add TDS URL entries for datasets listed in the log file."""

    data_log_file = os.path.join(PROJECT_ROOT,'prefect-workflow',LOG_FILE_NAME)
    dsids = parse_log_file(data_log_file)

    for dsid in dsids:
        print(f"Processing dataset ID: {dsid}")
        # moddify control file with TDS URL entry
        new_control_file = delete_breaking_control(dsid)
        print(f"Remained control file created at: {new_control_file}")
        # # remove the new control file after processing
        # os.remove(new_control_file)
        # print(f"Removed temporary control file: {new_control_file}")
        print("--------------------------------------------------")

if __name__ == "__main__":
    main()
