import re, os, glob, sys


# define global constants 
LOG_DIR = "/usr/local/tomcat/logs"
OUTPUT_FILE = os.path.join(LOG_DIR, "access_log_stats.txt")
HEADER = "date,total_requests,failed_requests,bytes_sent,bytes_success,subset_requests,opendap_requests,fileserver_requests,other_requests\n"

# regex pattern to extract date, path, status code, and bytes sent from log lines
log_pattern = re.compile(
    r'\[(\d{2}/\w{3}/\d{4}):\d{2}:\d{2}:\d{2}[^\]]*\] "\w+ ([^ ]+) [^"]*" (\d{3}) (\d+|-)'
)
date_from_filename = re.compile(
    r'localhost_access_log\.(\d{4}-\d{2}-\d{2})'
)


def process_log_file(log_file):
    """Process a single log file and return statistics as a dictionary.
    
    Parameters
    ----------
    log_file : str
        Path to the log file to process.
    
    Returns
    -------
    dict
        A dictionary containing statistics about the log file, including total requests,
        failed requests, bytes sent, bytes successfully sent, and counts of different request types.
    """
    stats = dict(total=0, failed=0, bytes_sent=0, bytes_success=0,
                 subset=0, opendap=0, fileserver=0, other=0)
    with open(log_file, "r", errors="replace", encoding="utf-8") as f:
        for line in f:
            m = log_pattern.search(line)
            if not m:
                continue
            _, path, status, bytes_raw = m.group(1), m.group(2), m.group(3), m.group(4)
            bval = int(bytes_raw) if bytes_raw != "-" else 0
            stats['total'] += 1
            stats['bytes_sent'] += bval
            if status != "200":
                stats['failed'] += 1
            else:
                stats['bytes_success'] += bval
            if "ncss" in path:
                stats['subset'] += 1
            elif "dodsC" in path:
                stats['opendap'] += 1
            elif "fileServer" in path:
                stats['fileserver'] += 1
            else:
                stats['other'] += 1
    return stats


def get_existing_dates():
    """Read the existing date in the stats file

    Returns
    -------
    set
        A set of date strings (YYYY-MM-DD) that are already present in the output file.
    """
    if not os.path.exists(OUTPUT_FILE):
        return set()
    dates = set()
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(',')
            if parts and re.match(r'\d{4}-\d{2}-\d{2}', parts[0]):
                dates.add(parts[0])
    return dates

if __name__ == "__main__":

    # Collect log files grouped by date
    log_files = sorted(glob.glob(os.path.join(LOG_DIR, "localhost_access_log.*")))
    print(f"Found {len(log_files)} log files")

    logs_by_date = {}
    for log_file in log_files:
        m = date_from_filename.search(os.path.basename(log_file))
        if m:
            logs_by_date.setdefault(m.group(1), []).append(log_file)

    existing_dates = get_existing_dates()
    missing_dates = sorted(set(logs_by_date.keys()) - existing_dates)

    if not missing_dates:
        print("No missing dates to process.")
        sys.exit(0)

    print(f"Processing {len(missing_dates)} missing date(s): {missing_dates}")

    rows = []
    for date in missing_dates:
        total = dict(total=0, failed=0, bytes_sent=0, bytes_success=0,
                    subset=0, opendap=0, fileserver=0, other=0)
        for log_file in logs_by_date[date]:
            s = process_log_file(log_file)
            for k in total:
                total[k] += s[k]
        rows.append((date, total))

    first_run = not os.path.exists(OUTPUT_FILE)
    mode = "w" if first_run else "a"

    with open(OUTPUT_FILE, mode, encoding="utf-8") as f:
        if first_run:
            f.write(HEADER)
        for date, s in rows:
            f.write(f"{date},{s['total']},{s['failed']},{s['bytes_sent']},{s['bytes_success']},{s['subset']},{s['opendap']},{s['fileserver']},{s['other']}\n")

    print(f"Wrote {len(rows)} row(s) to {OUTPUT_FILE}")
