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
import sys
import fsspec
import subprocess
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go


S3_STATS_PREFIX = "s3://gdex/tds-tomcat-logs"
S3_CLIENT_KWARGS = {
    "profile": "tdsbackup",
    "client_kwargs": {"endpoint_url": "https://boreas.hpc.ucar.edu:6443"},
}


def load_tds_usage_data(s3_path: str) -> pd.DataFrame:
    """
    Load TDS usage data from a stats txt file stored in the Boreas backup.
    The data is in the CSV format.

    Column names:
    date,total_requests,failed_requests,bytes_sent,bytes_success,
    subset_requests,opendap_requests,fileserver_requests,other_requests

    Parameters
    ----------
    s3_path : str
        Full s3:// path to the stats txt file to load.

    Returns
    -------
        pd.DataFrame: The TDS usage data.
    """
    # aws cli access:
    # aws s3 ls s3://gdex/tds-tomcat-logs/ --endpoint-url https://boreas.hpc.ucar.edu:6443/ --profile tdsbackup
    with fsspec.open(s3_path, mode="rb", **S3_CLIENT_KWARGS) as f:
        df = pd.read_csv(f, header=0)
    return df


def discover_dataset_ids() -> list[str]:
    """
    Discover which per-dataset stats files currently exist alongside the
    overall access_log_stats.txt, by listing access_log_stats_<dsid>.txt
    files in the Boreas backup.

    Returns
    -------
    list of str
        Dataset ids found, e.g. ["d633000"].
    """
    fs = fsspec.filesystem("s3", **S3_CLIENT_KWARGS)
    paths = fs.glob(f"{S3_STATS_PREFIX}/access_log_stats_*.txt")
    return [os.path.basename(p).removeprefix("access_log_stats_").removesuffix(".txt") for p in paths]


def load_all_datasets() -> dict[str, pd.DataFrame]:
    """
    Load the overall TDS usage data plus the usage data for every
    discovered per-dataset stats file.

    Returns
    -------
    dict of str -> pd.DataFrame
        Ordered mapping of label ("All Datasets", or a dataset id) to its
        usage data.
    """
    datasets = {"All Datasets": load_tds_usage_data(f"{S3_STATS_PREFIX}/access_log_stats.txt")}
    for dsid in discover_dataset_ids():
        datasets[dsid] = load_tds_usage_data(f"{S3_STATS_PREFIX}/access_log_stats_{dsid}.txt")
    return datasets


TRACES_PER_DATASET = 8  # 2 request lines + 2 byte lines + 4 request-type bars


def add_dataset_traces(fig, df: pd.DataFrame, visible: bool):
    """
    Add one dataset's full set of traces (requests, bytes, request types) to
    an existing 3-row subplot figure.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        Figure to add traces to, with 3 rows already set up via make_subplots.
    df : pd.DataFrame
        TDS usage data with columns: date, total_requests, failed_requests,
        bytes_sent, bytes_success, opendap_requests, fileserver_requests,
        other_requests, subset_requests.
    visible : bool
        Whether this dataset's traces should be shown initially.
    """
    LINE_WIDTH = 4
    MARKER_SIZE = 10

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
            legendgrouptitle_text="Requests",
            visible=visible,
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
            legendgroup="requests",
            visible=visible,
        ),
        row=1, col=1
    )

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
            legendgrouptitle_text="Bytes",
            visible=visible,
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
            legendgroup="bytes",
            visible=visible,
        ),
        row=2, col=1
    )

    # service usage breakdown
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["opendap_requests"],
            name="OPeNDAP",
            marker_color="#000000",
            legendgroup="request_types",
            visible=visible,
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["fileserver_requests"],
            name="File Server",
            marker_color="#233D4D",
            legendgroup="request_types",
            visible=visible,
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["other_requests"],
            name="Other",
            marker_color="#FE7F2D",
            legendgroup="request_types",
            visible=visible,
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["subset_requests"],
            name="Subset (NCSS)",
            marker_color="#60605E",
            legendgroup="request_types",
            legendgrouptitle_text="Request Types",
            visible=visible,
        ),
        row=3, col=1
    )


def create_stats_figure(datasets: dict[str, pd.DataFrame]):
    """
    Create a single interactive Plotly figure holding every dataset's traces,
    with only the first dataset visible by default. Switching which group is
    visible is handled externally (see build_combined_html's dropdown/JS).

    Parameters
    ----------
    datasets : dict of str -> pd.DataFrame
        Ordered mapping of label (e.g. "All Datasets", or a dataset id) to
        its usage data.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=("Requests", "Bytes", "Request Types"))

    for i, df in enumerate(datasets.values()):
        add_dataset_traces(fig, df, visible=(i == 0))

    fig.update_yaxes(title_text="Number of Requests", row=1, col=1)
    fig.update_yaxes(title_text="Bytes", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Number of Requests", row=3, col=1)

    # general layout settings
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", barmode="stack")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="lightgrey", griddash="dot")
    return fig


def build_combined_html(datasets: dict[str, pd.DataFrame], recent_days: int = 10) -> str:
    """
    Build a single HTML page with two sections: the most recent `recent_days`
    of usage, and the full history below it, each as the same 3-subplot figure.
    A shared dropdown above both sections switches which dataset ("All
    Datasets", or a specific dataset id) both sections display at once.

    Parameters
    ----------
    datasets : dict of str -> pd.DataFrame
        Ordered mapping of label (e.g. "All Datasets", or a dataset id) to
        its usage data, one row per day.
    recent_days : int
        Number of most recent days to show in the top section.

    Returns
    -------
    str
    """
    labels = list(datasets.keys())

    recent_datasets = {}
    history_datasets = {}
    for label, df in datasets.items():
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        history_datasets[label] = df
        recent_datasets[label] = df.tail(recent_days)

    recent_fig = create_stats_figure(recent_datasets)
    history_fig = create_stats_figure(history_datasets)

    recent_div = recent_fig.to_html(full_html=False, include_plotlyjs="cdn", div_id="recent-chart")
    history_div = history_fig.to_html(full_html=False, include_plotlyjs=False, div_id="history-chart")

    options_html = "\n".join(f'<option value="{i}">{label}</option>' for i, label in enumerate(labels))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>TDS Usage Statistics</title>
<style>
  body {{ font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; margin: 0; padding: 16px; }}
  h2 {{ margin: 8px 0; }}
  hr {{ border: none; border-top: 2px solid #dde3ea; margin: 32px 0; }}
  #dataset-select {{ font-size: 1rem; padding: 4px 8px; margin-bottom: 16px; }}
</style>
</head>
<body>
  <label for="dataset-select"><strong>Dataset:</strong></label>
  <select id="dataset-select" onchange="onDatasetChange()">
    {options_html}
  </select>

  <h2>Last {recent_days} Days</h2>
  {recent_div}
  <hr>
  <h2>Full History</h2>
  {history_div}

  <script>
    const TRACES_PER_DATASET = {TRACES_PER_DATASET};
    const DATASET_COUNT = {len(labels)};
    const CHART_IDS = ["recent-chart", "history-chart"];

    function onDatasetChange() {{
      const selected = parseInt(document.getElementById("dataset-select").value, 10);
      const visible = [];
      for (let i = 0; i < DATASET_COUNT; i++) {{
        for (let j = 0; j < TRACES_PER_DATASET; j++) {{
          visible.push(i === selected);
        }}
      }}
      CHART_IDS.forEach((id) => Plotly.restyle(id, {{ visible: visible }}));
    }}
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    # get the directory path of the current script
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # extract the TDS usage data (overall + per-dataset) from the Boreas backup
    datasets = load_all_datasets()

    # build the combined (recent + full history, switchable by dataset) HTML page
    html = build_combined_html(datasets, recent_days=10)

    # save the interactive Plotly figure as an HTML file
    with open(f"{dir_path}/../templates/tds_usage_stats.html", "w") as f:
        f.write(html)

    # use cp to copy html to special_projects/tds/tds_usage_stats.html
    result = subprocess.run(
        ["sudo", "-u", "gdexdata",
        "cp", f"{dir_path}/../templates/tds_usage_stats.html",
        "/gdex/data/special_projects/tds/tds_usage_stats.html"],
        check=True
    )
    if result.returncode != 0:
        print(f"Error: cp command failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    # use cp to copy html to special_projects/tds/tds_usage_dashboard.html 
    #  in case the dashboard HTML needs to be updated
    result = subprocess.run(
        ["sudo", "-u", "gdexdata",
        "cp", f"{dir_path}/../templates/tds_usage_dashboard.html",
        "/gdex/data/special_projects/tds/tds_usage_dashboard.html"],
        check=True
    )
    if result.returncode != 0:
        print(f"Error: cp command failed with exit code {result.returncode}")
        sys.exit(result.returncode)