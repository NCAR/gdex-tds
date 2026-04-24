#!/bin/bash -l
### Job Name
#PBS -N gdex-tds-data-autoscan
### Charging account
#PBS -A P43713000
### Request one chunk of resources with 1 CPU and 10 GB of memory
#PBS -l select=1:ncpus=1:mem=10GB
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

# git stash any local changes before switching branch
cd $USERHOME/gdex-tds/
echo "Changed directory to $(pwd)"
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $ORIGINAL_BRANCH"
git stash -u

# define cleanup function to restore original branch and stash on any exit
cleanup() {
    echo "Running cleanup: restoring branch $ORIGINAL_BRANCH"
    cd $USERHOME/gdex-tds/
    git checkout "$ORIGINAL_BRANCH"
    git stash pop 2>/dev/null || echo "No stash to restore"
    echo "Restored to branch with stashed changes: $ORIGINAL_BRANCH"
}
trap cleanup EXIT # run cleanup when script exits for any reason (success, error, interrupt)

# git get latest code from main branch before running the autoscan script
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
echo "Start auto_add_data_tds.py"
echo "******"
python -u auto_add_data_tds.py
EXIT_CODE=$?
echo "******"

if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: auto_add_data_tds.py failed with exit code $EXIT_CODE"
    # Send email notification
    SUBJECT="TDS Data Autoscan Failed - Exit Code $EXIT_CODE"
    BODY="The TDS data autoscan script failed on $(date).

        Exit Code: $EXIT_CODE
        Job: $PBS_JOBID
        Host: $(hostname)
        Working Directory: $(pwd)

        Please check the log file for details:
        $PBS_O_WORKDIR/gdex-tds-data-autoscan.o$PBS_JOBID"
    
    echo "$BODY" | mail -s "$SUBJECT" $USER@ucar.edu
    echo "Error notification email sent to $USER@ucar.edu"
    exit $EXIT_CODE
else
    echo "Finished auto_add_data_tds.py successfully"
fi

# check if the log file from auto_add_data_tds.py exists and get the log file name for git push in the next step
LOG_FILE="auto_add_data_tds_$(date +%Y-%m-%d)*.log"
MATCHED_LOG=$(ls $LOG_FILE 2>/dev/null | head -1)

if [[ -z "$MATCHED_LOG" ]]; then
    echo "ERROR: No log file matching $LOG_FILE found. Skipping."
    exit 1
fi
echo "Using log file: $MATCHED_LOG"

# create new branch, delete first if it already exists from a previous run today
git branch -D auto_add_data_tds_$(date +%Y-%m-%d) 2>/dev/null || true
git push origin --delete auto_add_data_tds_$(date +%Y-%m-%d) 2>/dev/null || true
git checkout -b auto_add_data_tds_$(date +%Y-%m-%d)

# add new data xml and log file to git, commit and push to remote branch
cd $USERHOME/gdex-tds/
git add prefect-workflow/auto_add_data_tds_*.log
git add rda-tds/content/catalog.xml
git add rda-tds/content/catalog_*.xml
git commit -m "Auto add data to TDS on $(date +%Y-%m-%d)"
git push origin auto_add_data_tds_$(date +%Y-%m-%d)

# delete local branch after push (remote branch is kept for PR)
git checkout main
git pull origin main
git branch -d auto_add_data_tds_$(date +%Y-%m-%d) 2>/dev/null || true
