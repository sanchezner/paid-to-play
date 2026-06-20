import mlflow
import pandas as pd

def load_models(tracking_uri):
    mlflow.set_tracking_uri(tracking_uri)
    return (
        mlflow.pyfunc.load_model("models:/bpm-projector@champion"),
        mlflow.pyfunc.load_model("models:/bpm-to-cap-trend@champion")
    )


def predict_bpm(features_df, feature_columns, model):
    X = features_df[feature_columns]
    bpm_predictions = model.predict(X)
    return bpm_predictions


def predict_trend_cap_pct(predicted_bpm, model):
    payload = pd.DataFrame({"predicted_bpm": predicted_bpm})
    trend_cap_pct = model.predict(payload)["trend_cap_pct"]
    return trend_cap_pct