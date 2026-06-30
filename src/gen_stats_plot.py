"""
This script is designed to generate the interactive statistics plot of 
the TDS usage. 

Steps:
1. Load the TDS usage data from the txt file from the Boreas backuop
    - the python script generating the statistics and backed up 
      are located inside the rda-tds-helm/scripts/log_stats.py file.
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

    Column names:
    date,total_requests,failed_requests,bytes_sent,bytes_success,
    subset_requests,opendap_requests,fileserver_requests,other_requests

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


def create_stats_figure(df: pd.DataFrame):
    """
    Create the interactive Plotly figure from TDS usage data.

    Parameters
    ----------
    df : pd.DataFrame
        TDS usage data with columns: date, total_requests, failed_requests,
        bytes_sent, bytes_success.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    LINE_WIDTH = 4
    MARKER_SIZE = 10
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=("Requests", "Bytes", "Request Types"))

    # number of requests
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
    fig.update_yaxes(title_text="Number of Requests", row=1, col=1)

    # Bytes request
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
    fig.update_yaxes(title_text="Bytes", row=2, col=1)

    # service usage breakdown
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["opendap_requests"],
            name="OPeNDAP",
            marker_color="#000000",
            legendgroup="request_types"
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["fileserver_requests"],
            name="File Server",
            marker_color="#233D4D",
            legendgroup="request_types"
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["other_requests"],
            name="Other",
            marker_color="#FE7F2D",
            legendgroup="request_types"
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["subset_requests"],
            name="Subset (NCSS)",
            marker_color="#EAECF0",
            legendgroup="request_types",
            legendgrouptitle_text="Request Types"
        ),
        row=3, col=1
    )
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Number of Requests", row=3, col=1)

    # general layout settings
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", barmode="stack")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="lightgrey", griddash="dot")
    return fig


if __name__ == "__main__":
    # get the directory path of the current script
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # extract the TDS usage data from the Boreas backup
    df = load_tds_usage_data()

    # create the interactive Plotly figure
    fig = create_stats_figure(df)

    # save the interactive Plotly figure as an HTML file
    fig.write_html(f"{dir_path}/../tds_usage_stats.html")
    


