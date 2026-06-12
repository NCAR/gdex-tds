import re, os, glob
from datetime import datetime

LOG_DIR = "/usr/local/tomcat/logs"
OUTPUT_FILE = os.path.join(LOG_DIR, "access_log_stats.txt")

# parse log line
# 127.0.0.1 - - [12/Jun/2026:04:00:01 +0000] "GET /thredds/catalog.html HTTP/1.1" 200 1234
log_pattern = re.compile(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}):\d{2}[^\]]*\] "\w+ ([^ ]+) [^"]*" (\d{3}) (\d+|-)')

# allocate statistics
total_requests = int(0)
failed_requests = int(0)
bytes_sent = int(0)
bytes_success = int(0)
subset_requests = int(0)
opendap_requests = int(0)
fileserver_requests = int(0)
other_requests = int(0)

# access_patterns = [
#     'ncss',
#     'dodsC',
#     'fileServer'
# ]

log_files = sorted(glob.glob(os.path.join(LOG_DIR, "localhost_access_log.*")))
print(f"Found {len(log_files)} log files")

for log_file in log_files:
    with open(log_file, "r", errors="replace", encoding="utf-8") as f:
        for line in f:
            m = log_pattern.search(line)
            if not m:
                continue

            # parse log line
            date_str, path, status, bytes_raw = m.group(1), m.group(2), m.group(3), m.group(4)

            # update statistics
            total_requests += 1
            if status != "200":
                failed_requests += 1
            else:
                bytes_success += int(bytes_raw) if bytes_raw != "-" else 0
            bytes_sent += int(bytes_raw) if bytes_raw != "-" else 0

            # check access patterns
            if "ncss" in path:
                subset_requests += 1
            elif "dodsC" in path:
                opendap_requests += 1
            elif "fileServer" in path:
                fileserver_requests += 1
            else:
                other_requests += 1

# test if the OUTPUT_FILE already exists
if os.path.exists(OUTPUT_FILE):
    # append to the file
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"{total_requests},{failed_requests},{bytes_sent},{bytes_success},{subset_requests},{opendap_requests},{fileserver_requests},{other_requests}\n")
else:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("total_requests,failed_requests,bytes_sent,bytes_success,subset_requests,opendap_requests,fileserver_requests,other_requests\n")
        f.write(f"{total_requests},{failed_requests},{bytes_sent},{bytes_success},{subset_requests},{opendap_requests},{fileserver_requests},{other_requests}\n")

print(f"Report written to {OUTPUT_FILE} for date {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
