import mlflow
import os
from dotenv import load_dotenv

load_dotenv()

tracking_uri = os.getenv('TRACKING_URI')
mlflow.set_tracking_uri(tracking_uri)

model = mlflow.pyfunc.load_model("models:/bpm-projector@champion")

print(type(model))