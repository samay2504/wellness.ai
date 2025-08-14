"""Quick GCS verification script.

Lists objects in a Google Cloud Storage bucket to verify uploads.

Features:
  - Bucket autodetected from env GCS_BUCKET (fallback AWS_S3_BUCKET) or --bucket
  - Credentials autodetected from GOOGLE_APPLICATION_CREDENTIALS / GCS_CREDENTIALS_FILE
  - Filter by --prefix
  - Limit results with --limit
  - Summaries: total objects, total size, events/user counts (for events/ prefix)
  - Optional JSON output (--json)
  - Expect specific object path(s) (--expect path1 --expect path2) -> non‑zero exit if any missing
  - Filter by recently updated --since-mins (minutes ago)
  - Exit codes: 0 success, 2 missing expected objects, 3 bucket/list failure

Usage examples:
  python verify_gcs_objects.py --prefix events/ --limit 25
  python verify_gcs_objects.py --prefix events/ --since-mins 10 --json
  python verify_gcs_objects.py --expect events/123/abc.json --expect batches/2025/08/15/file.json

Windows PowerShell shortcut (with explicit bucket):
  $env:GCS_BUCKET="wellness-ai-data"; python verify_gcs_objects.py --prefix events/ --limit 10

Requires: google-cloud-storage (already in requirements.txt)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

try:
    from google.cloud import storage as gcs_storage  # type: ignore
except ImportError as e:  # pragma: no cover - handled at runtime
    print("google-cloud-storage not installed. Install with: pip install google-cloud-storage", file=sys.stderr)
    sys.exit(3)


def load_client(creds_path: str | None):
    if creds_path and not os.path.exists(creds_path):
        raise FileNotFoundError(f"Credentials file not found: {creds_path}")
    if creds_path:
        return gcs_storage.Client.from_service_account_json(creds_path)
    # Fall back to default creds (ADC) if available
    return gcs_storage.Client()


def human_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024.0:
            return f"{n:3.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify and list GCS bucket objects")
    p.add_argument("--bucket", help="GCS bucket name (defaults env GCS_BUCKET/AWS_S3_BUCKET)")
    p.add_argument("--prefix", default="", help="Only list objects with this prefix")
    p.add_argument("--limit", type=int, default=100, help="Max objects to display (0 = no limit)")
    p.add_argument("--json", action="store_true", help="Output JSON only (machine readable)")
    p.add_argument("--expect", action="append", default=[], help="Object path expected to exist (can repeat)")
    p.add_argument("--since-mins", type=int, default=None, help="Only include objects updated within last N minutes")
    p.add_argument("--credentials", help="Explicit path to service account JSON (overrides env)")
    p.add_argument("--timeout", type=int, default=30, help="Per list call timeout seconds")
    return p.parse_args()


def list_objects(client, bucket_name: str, prefix: str, since_dt: datetime | None, limit: int, timeout: int):
    bucket = client.bucket(bucket_name)
    # Using client.list_blobs gives iterator; keep metadata only
    blobs_iter = client.list_blobs(bucket_name, prefix=prefix, timeout=timeout)
    results = []
    for idx, blob in enumerate(blobs_iter):
        if since_dt and blob.updated and blob.updated.replace(tzinfo=timezone.utc) < since_dt:
            continue
        results.append({
            "name": blob.name,
            "size": blob.size or 0,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "content_type": blob.content_type,
        })
        if limit and len(results) >= limit:
            break
    return results


def summarize(objects: List[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
    total_size = sum(o["size"] for o in objects)
    summary = {
        "count": len(objects),
        "total_size_bytes": total_size,
        "total_size_human": human_size(total_size),
    }
    if prefix.startswith("events/") or prefix == "events/" or prefix == "":
        # try to derive user counts for objects under events/<user_id>/...
        user_counts: Dict[str, int] = {}
        for o in objects:
            parts = o["name"].split("/")
            if len(parts) >= 3 and parts[0] == "events":
                user_counts[parts[1]] = user_counts.get(parts[1], 0) + 1
        if user_counts:
            summary["events_per_user"] = user_counts
    return summary


def main():  # pragma: no cover - CLI tool
    args = parse_args()

    bucket = args.bucket or os.environ.get("GCS_BUCKET") or os.environ.get("AWS_S3_BUCKET")
    if not bucket:
        print("Bucket not specified. Use --bucket or set GCS_BUCKET.", file=sys.stderr)
        sys.exit(3)

    creds_path = (
        args.credentials
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or os.environ.get("GCS_CREDENTIALS_FILE")
        or os.path.abspath(os.path.join(os.path.dirname(__file__), "configs", "credentials.json"))
    )

    since_dt = None
    if args.since_mins is not None:
        since_dt = datetime.now(timezone.utc) - timedelta(minutes=args.since_mins)

    try:
        client = load_client(creds_path if os.path.exists(creds_path) else None)
    except Exception as e:
        print(f"Failed to initialize GCS client: {e}", file=sys.stderr)
        sys.exit(3)

    try:
        objects = list_objects(client, bucket, args.prefix, since_dt, args.limit, args.timeout)
    except Exception as e:
        print(f"Failed to list objects: {e}", file=sys.stderr)
        sys.exit(3)

    summary = summarize(objects, args.prefix)

    missing = []
    if args.expect:
        # If limit truncated listing, we may need full scan for expected objects not in initial list
        names = {o["name"] for o in objects}
        need_full_scan = any(exp not in names for exp in args.expect) and args.limit and len(objects) == args.limit
        if need_full_scan:
            try:
                full_objects = list_objects(client, bucket, args.prefix, since_dt, 0, args.timeout)
                names = {o["name"] for o in full_objects}
                objects = full_objects  # upgrade list for reporting
                summary = summarize(objects, args.prefix)
            except Exception:
                pass
        for exp in args.expect:
            if exp not in names:
                missing.append(exp)

    result = {
        "bucket": bucket,
        "prefix": args.prefix,
        "limit": args.limit,
        "returned": len(objects),
        "since_filter": args.since_mins,
        "objects": objects,
        "summary": summary,
        "expected": args.expect,
        "missing_expected": missing,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Bucket: {bucket}")
        print(f"Prefix: '{args.prefix}'  Returned: {len(objects)}  Filter since(mins): {args.since_mins}")
        print(f"Total size: {summary['total_size_human']} ({summary['total_size_bytes']} bytes)")
        if 'events_per_user' in summary:
            print("Events per user:")
            for user, cnt in sorted(summary['events_per_user'].items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]):
                print(f"  {user}: {cnt}")
        if objects:
            print("\nObjects:")
            for o in objects:
                updated = o['updated'] or 'n/a'
                print(f"  {updated}  {human_size(o['size']):>8}  {o['name']}")
        if args.expect:
            if missing:
                print("\nMissing expected objects:")
                for m in missing:
                    print(f"  {m}")
            else:
                print("\nAll expected objects present.")

    if missing:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
