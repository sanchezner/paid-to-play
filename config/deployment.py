import os
from dotenv import load_dotenv

load_dotenv()

s3_bucket = os.getenv('S3_BUCKET')
conn_string = os.getenv('CONN_STRING')
tracking_uri = os.getenv('TRACKING_URI')