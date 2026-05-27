# Backup and Restore

The `tds-persist` PVC is backed up nightly to the GDEX S3 appliance
(`https://boreas.hpc.ucar.edu:6443`, bucket `gdex`, prefix
`tds-data/`) via a Kubernetes CronJob defined in the chart.

This document describes how the backup works for this application and
how to restore from it, both for a single file at a point in time and
for a full PVC.

## Overview

| Component         | Where                                                    |
|-------------------|----------------------------------------------------------|
| Source data       | `tds-persist` PVC (mounted at `/data` in the backup pod) |
| Destination       | `s3://gdex/tds-data/` on the GDEX appliance              |
| Schedule          | 04:17 UTC nightly (configured via `backup.schedule`)     |
| Credentials       | `backup-s3-creds` secret in the deployment namespace     |
| Bucket versioning | Enabled — overwrites and deletes retain previous bytes   |
| Lifecycle policy  | Noncurrent versions expire after 90 days                 |
| Tool              | `rclone copy` (never `sync`; deletions don't propagate)  |
| Run reports       | `s3://gdex/tds-data/_reports/<run-id>.txt` per run       |

The CronJob template lives at `app-chart/templates/pv-s3-backup.yaml`
and is gated by `backup.enabled` in values.

## What's in the backup

The TDS index dataset directories (`/data/d*`) on the PVC — roughly
~256 GiB across ~3 million files at last measurement. The
data-bearing directories are backed up nightly; the runtime scratch
state below is deliberately excluded.

### What's excluded (and why)

The PVC holds both persistent data and scratch state used by Tomcat,
TDS, and TDM. Scratch is regenerable and would only add noise to the
backup, so it's filtered out via `--exclude` patterns:

| Path                          | What it is             | Why excluded     |
|-------------------------------|------------------------|------------------|
| `tds-overflow/**`             | Tomcat work, temp, JVM heap dumps | Regenerable scratch (~36 GiB, high churn) |
| `tds-temp-cache-cdm/**`       | TDS CDM cache          | Rebuilt by TDS on demand |
| `tds-temp-cache-ncss/**`      | TDS NCSS cache         | Rebuilt by TDS on demand |
| `tds-temp-cache-wcs/**`       | TDS WCS cache          | Rebuilt by TDS on demand |
| `tds-temp-cache-edal-java/**` | TDS WMS tile cache     | Rebuilt by TDS on demand |
| `tds-temp-logs/**`            | TDS server logs        | Shipped elsewhere (Loki/promtail) |
| `tdm-logs/**`                 | TDM logs               | Shipped elsewhere (Loki/promtail) |
| `*.tmp`                       | TDM atomic-write tempfiles | Race condition with rclone — these get renamed away mid-backup |

The exclude list lives in `backup.rclone.extraFlags` in the chart's
values file. If TDS or TDM ever start writing new scratch directories,
add them to that list.

### What's preserved

- **Symlinks are preserved as symlinks** (`--links`). Stored in S3 as
  `.rclonelink` placeholder files; on restore with `--links` they're
  recreated as real symlinks.
- **Permission-denied paths are logged and tolerated.** The backup pod
  runs as UID 1000 (matches PVC ownership). The report would surface
  any permission issues.
- **Race conditions are logged and tolerated.** TDM may rename files
  between rclone's directory listing and read; `*.tmp` files are
  excluded but if a non-`.tmp` file races, the wrapper logs it and
  doesn't fail the job. Counted separately in the report.

## How the CronJob decides success or failure

| rclone exit | Other errors | Job result | Meaning                          |
|-------------|--------------|------------|----------------------------------|
| 0           | 0            | Success    | Clean run                        |
| 6           | 0            | Success    | Only expected errors (see report)|
| anything else | -          | Fail       | Real problem — Alertmanager fires|

"Expected errors" means permission-denied paths, broken symlinks, or
race conditions where a file disappeared between listing and read.
Anything else (network failures, auth errors, the appliance being
unreachable, etc.) fails the Job loudly.

If the "Race conditions" count in the report climbs into the dozens
or hundreds per run, that's a signal the exclude list isn't catching
something TDM is writing transiently. Worth investigating and
extending the excludes.

## Restoring a single file

Use this when one file got corrupted, accidentally modified, or
deleted on the live PVC, and you want a clean copy from S3.

### The current backed-up version

The simplest case. From a pod with rclone and the backup credentials
(easiest: spin up a debug pod modeled on the CronJob, or use any pod
where `rclone` and the secret are available):

```sh
rclone copy \
  --links \
  gdex:gdex/tds-data/d628001/some/path/file.grb \
  /tmp/restored/
```

Then move it into place on the PVC, with whatever ownership/mode the
original had:

```sh
chown 1000:1000 /tmp/restored/file.grb
cp -p /tmp/restored/file.grb /data/d628001/some/path/file.grb
```

### An older version (point-in-time restore)

Because bucket versioning is enabled, every overwrite or delete keeps
the previous bytes for up to 90 days. To restore a specific historical
version, use boto3 or the AWS CLI — rclone doesn't have great
version-aware support.

```sh
export AWS_ACCESS_KEY_ID=$(kubectl get secret backup-s3-creds \
  -o jsonpath='{.data.access_key}' | base64 -d)
export AWS_SECRET_ACCESS_KEY=$(kubectl get secret backup-s3-creds \
  -o jsonpath='{.data.secret_key}' | base64 -d)
export AWS_DEFAULT_REGION=us-east-1
ENDPOINT=https://boreas.hpc.ucar.edu:6443

# List all versions of a specific object
aws --endpoint-url "${ENDPOINT}" s3api list-object-versions \
  --bucket gdex \
  --prefix tds-data/d628001/some/path/file.grb

# Output includes Versions[] (each with VersionId, LastModified, Size)
# and DeleteMarkers[] if the object was deleted. Pick the VersionId
# you want, then:

aws --endpoint-url "${ENDPOINT}" s3api get-object \
  --bucket gdex \
  --key tds-data/d628001/some/path/file.grb \
  --version-id "<the-version-id>" \
  /tmp/restored-file.grb
```

Notes:

- `IsLatest: true` is the current version. Older versions have
  `IsLatest: false`.
- A delete marker means the object was deleted. We don't issue
  deletes from the backup process; a manual purge would create one.
  The object's content lives in the prior version, accessible by
  VersionId.
- Versions older than ~90 days may have been removed by the lifecycle
  policy. If you need longer retention for a specific file, copy it
  somewhere else.

## Restoring the entire PVC

Use this for catastrophic data loss — the underlying PV is gone, the
PVC is corrupted, or someone ran something they shouldn't have.

### Prerequisites

- A new (empty) PVC of sufficient size. The current `tds-persist` is 1Ti.
- The `backup-s3-creds` secret in the same namespace.
- Several hours of patience. The initial seed of ~256 GiB took ~3 hours
  over the appliance link.

### Procedure

1. Provision the replacement PVC. Use the same name (`tds-persist`) or
   pick a temporary one and rename later.

2. Run a restore pod that mounts the new PVC and runs rclone in the
   reverse direction. A minimal manifest:

   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: tds-restore
     namespace: rda
   spec:
     restartPolicy: Never
     securityContext:
       runAsNonRoot: true
       runAsUser: 1000
       runAsGroup: 1000
       fsGroup: 1000
     containers:
       - name: rclone
         image: docker.io/rclone/rclone:1.74
         command: ["/bin/sh", "-c"]
         args:
           - |
             set -eu
             export RCLONE_CONFIG=/tmp/rclone.conf
             cat > "${RCLONE_CONFIG}" <<EOF
             [src]
             type = s3
             provider = Other
             endpoint = https://boreas.hpc.ucar.edu:6443
             force_path_style = true
             env_auth = true
             EOF
             rclone copy \
               --links \
               --transfers 8 \
               --checkers 16 \
               --s3-chunk-size 64M \
               --stats 1m \
               --stats-one-line \
               --metadata \
               src:gdex/tds-data/ /data/
         env:
           - name: AWS_ACCESS_KEY_ID
             valueFrom:
               secretKeyRef: { name: backup-s3-creds, key: access_key }
           - name: AWS_SECRET_ACCESS_KEY
             valueFrom:
               secretKeyRef: { name: backup-s3-creds, key: secret_key }
         volumeMounts:
           - name: target
             mountPath: /data
         resources:
           requests: { cpu: "200m", memory: "256Mi" }
           limits:   { cpu: "2",    memory: "6Gi"   }
     volumes:
       - name: target
         persistentVolumeClaim:
           claimName: tds-persist
   ```

3. Monitor progress:

   ```sh
   kubectl logs -f -n rda tds-restore
   ```

4. When rclone exits 0, verify:

   ```sh
   # File count and size should be close to the backup totals
   kubectl exec tds-restore -- du -sh /data
   kubectl exec tds-restore -- find /data -type f | wc -l
   ```

5. Delete the restore pod and bring TDS back up against the restored PVC.

### What you DON'T get back from a restore

- **The scratch/cache/log directories.** They were excluded from the
  backup. TDS and TDM will recreate them as needed; the first startup
  after restore will be slower because caches are cold.
- **POSIX mode bits.** S3 doesn't store them. Restored files will have
  the umask defaults of the restore pod.
- **Ownership across UIDs.** If the restore pod runs as UID 1000,
  everything comes back owned by 1000:1000 (which is correct). If the
  pod runs as anything else, you'll need a `chown -R 1000:1000 /data`
  after restore.

Symlinks DO come back as symlinks, provided the restore is done with
rclone using the `--links` flag — see the example manifest above.

## Testing the restore

The restore procedure is only as good as the last time you tested
it. Recommended: do a quarterly restore drill into a throwaway PVC,
spot-check a handful of files, then tear down the test PVC. Calendar
reminder, not optional.

## Operational notes

- **First-time backup setup** including the manual seed, lifecycle
  policy, and bucket versioning configuration was done out-of-band
  and is not re-applied by the chart. If the bucket itself is ever
  recreated, those steps need to be redone — see the
  `apply_lifecycle.py` and `inspect_gdex.py` scripts in the
  `pv-backup/` directory of the gdex-web-portal repo.
- **Schedule.** TDS backup runs at 04:17 UTC, staggered from
  gdex-web's 02:17 UTC to avoid both saturating the link to Boreas
  simultaneously. Override `backup.schedule` in values if you want
  to shift it (e.g., to avoid a TDM regeneration window).
- **Run reports** are uploaded to `_reports/` even on successful
  runs. They list any permission-denied paths, broken symlinks, and
  race-condition errors encountered, which is useful for spotting
  source-side issues without having to trawl Loki logs.
- **rclone version bumps.** The image tag is pinned in the chart
  defaults. Don't use `:latest` or `:master` — rolling tags break
  unattended jobs in surprising ways.