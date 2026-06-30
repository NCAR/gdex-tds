# THREDDS helper scripts and monitoring

### createCTL.py
Used to create a rda control file for dsrqst

### createXML.py
Creates a THREDDS XML file for a given dataset. Does not update `catalog.xml`.

### gen_stats_plot.py
Create a plotly html output in the root dir based on the daily stats generated and backed up on Boreas

### createAllXMLS.bash
Calls `createXML.py` for each dataset
