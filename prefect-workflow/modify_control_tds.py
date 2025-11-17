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
from add_control_tds import create_ctl, get_control_file, parse_log_file

# setup log file name to be read
LOG_FILE_NAME = "auto_add_data_tds_2025-11-14-12_31_54.log"

# Get the directory of this script and the project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Project root directory


def modify_control_file(dsid: str) -> str:
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

    # get original control file
    old_control_lines = get_control_file(dsid)

    # modify the origin control lines
    modified_control_lines = [old_control_lines[0]]
    for line in old_control_lines[1:]:
        infos = line.strip().split('<:>')
        group_index = infos[2]
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

        for new_line in new_control_lines:
            new_infos = new_line.strip().split('<:>')
            new_group_index = new_infos[2]
            new_url = new_infos[9]
            if group_index == new_group_index:
                # update the url
                line = line.replace(url, new_url)
                modified_control_lines.append(line)
                break


    # write to new control file
    control_file_path = os.path.join(PROJECT_ROOT,'prefect-workflow',f"{dsid}_new.ctl")

    with open(control_file_path, 'w', encoding='utf-8') as f:
        for line in modified_control_lines:
            f.write(line + '\n')

    return control_file_path

modify_control_file(dsid="d734000")

def modify_tds_url(dsid: str, new_control_file: str):
    """Modify the TDS URL entry to the dataset page using the control file.

    Parameters
    ----------
    dsid : str
        Dataset ID.
    new_control_file : str
        Path to the new control file.
    """

    command = ["dsrqst", "-sc", "-ds", dsid, "-if", new_control_file, "-md"]

    # Run the command
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Successfully modified TDS URL for dataset {dsid}")
        print(f"STDOUT: {result.stdout}")
        return result

    except subprocess.CalledProcessError as err_result:
        print(f"Failed to modify TDS URL for dataset {dsid} with exit code {err_result.returncode}")
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
        new_control_file = modify_control_file(dsid)
        print(f"Modified control file created at: {new_control_file}")
        # modify TDS URL entry using the new control file
        dsrqst_result = modify_tds_url(dsid, new_control_file)
        if dsrqst_result.returncode == 1:
            # DO NOT remove the new control file if failed (easier to track the issue)
            log_error = f"Failed to modify TDS URL for {dsid} for web access."
            print(log_error)
            continue
        log_info = f"Successfully modified TDS URL for {dsid} for web access."
        print(log_info)
        # # remove the new control file after processing
        # os.remove(new_control_file)
        # print(f"Removed temporary control file: {new_control_file}")
        print("--------------------------------------------------")

if __name__ == "__main__":
    main()
