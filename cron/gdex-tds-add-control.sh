#!/bin/bash -l
### Job Name
#PBS -N gdex-tds-add-control
### Charging account
#PBS -A P43713000
### Request one chunk of resources with 1 CPU and 1 GB of memory
#PBS -l select=1:ncpus=1:mem=1GB
### Allow job to run up to 30 minutes
#PBS -l walltime=30:00
### Route the job to the casper queue
#PBS -q gdex
### Join output and error streams into single file
#PBS -j oe

# Environment Management
module --force purge
USERHOME=/glade/u/home/$USER
# module load conda

# source venv
source $USERHOME/gdex_work/.venv/bin/activate

# make sure to have the latest main branch code
cd $USERHOME/gdex-tds/
git checkout main
git pull origin main

### Job commands start here
cd $USERHOME/gdex-tds/prefect-workflow/
echo "Changed directory to $(pwd)"
time=$(date)
echo "--------------------------------"
echo "Current time: $time"
echo "--------------------------------"
echo "PBS job started"
which python
python --version
echo "--------------------------------"
echo "Start add_control_tds.py"
echo "******"
LOG_FILE="auto_add_data_tds_$(date +%Y-%m-%d)*.log"
MATCHED_LOG=$(ls $LOG_FILE 2>/dev/null | head -1)

if [[ -z "$MATCHED_LOG" ]]; then
    echo "ERROR: No log file matching $LOG_FILE found. Skipping."
    exit 1
fi
echo "Using log file: $MATCHED_LOG"
python -u add_control_tds.py "$MATCHED_LOG"
EXIT_CODE=$?
echo "******"

if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: add_control_tds.py failed with exit code $EXIT_CODE"
    # Send email notification
    SUBJECT="TDS Data Autoscan Failed - Exit Code $EXIT_CODE"
    BODY="The TDS data autoscan script failed on $(date).

Exit Code: $EXIT_CODE
Job: $PBS_JOBID
Host: $(hostname)
Working Directory: $(pwd)

Please check the log file for details:
$PBS_O_WORKDIR/gdex-tds-add-control.o$PBS_JOBID"
    
    echo "$BODY" | mail -s "$SUBJECT" $USER@ucar.edu
    echo "Error notification email sent to $USER@ucar.edu"
    exit $EXIT_CODE
else
    echo "Finished add_control_tds.py successfully"
fi
