"""
This script is designed to generate the interactive statistics plot of 
the TDS usage. 

Steps:
1. Load the TDS usage data from the txt file from the Boreas backuop
2. Plot the data using plotly and save it as an interactive HTML file.
"""
import os
import fsspec
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go


def load_tds_usage_data() -> pd.DataFrame:
    """
    Load the TDS usage data from the txt file stored in the Boreas backup.
    The data is in the CSV format.

    date,total_requests,failed_requests,bytes_sent,bytes_success,subset_requests,opendap_requests,fileserver_requests,other_requests

    Returns
    -------
        pd.DataFrame: The TDS usage data.
    """

    # Load the TDS usage data from the txt file stored in the Boreas backup.
    # aws cli access:
    # aws s3 ls s3://gdex/tds-tomcat-logs/ --endpoint-url https://boreas.hpc.ucar.edu:6443/ --profile tdsbackup
    s3_path = "s3://gdex/tds-tomcat-logs/access_log_stats.txt"
 
    with fsspec.open(
        s3_path,
        mode="rb",
        profile="tdsbackup",
        client_kwargs={"endpoint_url": "https://boreas.hpc.ucar.edu:6443"}
    ) as f:
        df = pd.read_csv(f, header=0)
    return df


if __name__ == "__main__":
    # get the directory path of the current script
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # load the csv file from the Boreas backup
    df = load_tds_usage_data()

    # create the plotly interactive plot
    # request number plot
    fig = make_subplots(rows=2, cols=1, subplot_titles=("Requests", "Bytes"))
    LINE_WIDTH = 4
    MARKER_SIZE = 6
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["total_requests"],
            name="Total Requests",
            mode="lines+markers",
            line=dict(color="#FF9E20", width=LINE_WIDTH),
            marker=dict(size=MARKER_SIZE),
            legendgroup="requests",
            legendgrouptitle_text="Requests"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["failed_requests"],
            name="Failed Requests",
            mode="lines+markers",
            line=dict(color="#BE1A1A", width=LINE_WIDTH),
            marker=dict(size=MARKER_SIZE),
            legendgroup="requests"
        ),
        row=1, col=1
    )
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Number of Requests", row=1, col=1)

    # request byte plot
    fig.add_trace(
        go.Scatter(
            x=df["date"], 
            y=df["bytes_sent"], 
            name="Bytes Sent", 
            mode="lines+markers",
            line=dict(color="#FF9E20", width=LINE_WIDTH), 
            marker=dict(size=MARKER_SIZE),
            legendgroup="bytes", 
            legendgrouptitle_text="Bytes"
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"], 
            y=df["bytes_success"], 
            name="Bytes Success", 
            mode="lines+markers",
            line=dict(color="#215E61", width=LINE_WIDTH), 
            marker=dict(size=MARKER_SIZE),
            legendgroup="bytes"
        ),
        row=2, col=1
    )
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Bytes", row=2, col=1)
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="lightgrey", griddash="dot")

    # save the plot as an interactive HTML file
    fig.write_html(f"{dir_path}/../tds_usage_stats.html")
    


