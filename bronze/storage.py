import boto3, json
from config.deployment import s3_bucket

s3_client = boto3.client("s3")

def upload_json(data, key):
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=key,
        Body=json.dumps(data, indent=4, default=str),
        ContentType="application/json",
    )