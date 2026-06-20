import boto3, json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from config.deployment import s3_bucket, conn_string


s3_client = boto3.client("s3")


def list_keys(prefix):
    paginator = s3_client.get_paginator("list_objects_v2")
    keys = []

    for page in paginator.paginate(Bucket=s3_bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])

    return keys


def pull_json(key):
    response = s3_client.get_object(
        Bucket=s3_bucket,
        Key=key
    )
    json_response = json.loads(response['Body'].read())
    return json_response


def get_engine():
    return create_engine(conn_string)


def upsert_with_visibility(engine, *, staging_table, insert_sql, label):
    """Run an INSERT ... SELECT ... WHERE EXISTS ... ON CONFLICT DO NOTHING and
    report how many staging rows actually landed.

    Why: ON CONFLICT DO NOTHING and the FK guard both silently drop rows. A
    silent drop is a worse failure mode than a loud crash — you want the delta
    surfaced so missing data is observable, not invisible.

    `insert_sql` must end with `RETURNING 1` so we can count actual inserts;
    rowcount alone isn't reliable across drivers when combined with ON CONFLICT.
    """
    with engine.begin() as conn:
        staging_count = conn.execute(
            text(f"SELECT COUNT(*) FROM {staging_table}")
        ).scalar()
        inserted_count = len(conn.execute(text(insert_sql)).fetchall())

    skipped = staging_count - inserted_count
    if skipped:
        print(
            f"[warn] {label}: {inserted_count}/{staging_count} rows inserted "
            f"({skipped} skipped: FK miss or already present)"
        )
    else:
        print(f"[ok] {label}: {inserted_count}/{staging_count} rows inserted")