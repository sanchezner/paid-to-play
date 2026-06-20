from __future__ import annotations
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import mlflow
import mlflow.xgboost
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from bronze.gamelogs import get_train_season_splits
from config.domain import training_start_season
from silver.storage import get_engine
from mlflow.models import infer_signature

load_dotenv()

tracking_uri = os.getenv('TRACKING_URI')
experiment_name = "bpm-projection"
target_column = "label_bpm"
feature_set_version = "v1"

artifact_dir = Path("artifacts/bpm-projector")


def load_feature_snapshots():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM feature_snapshots", engine)


def select_feature_columns(df):
    excluded_columns = ['nba_id', 'bref_id', 'season', 'games_seen', 'snapshot_date', 'label_bpm', 'label_games_played', 'created_at']
    return [column for column in df.columns if column not in excluded_columns]


def split_by_season(df, season_splits=None):
    season_splits = season_splits or get_train_season_splits()

    eligible_df = df[~df["season"].isin(season_splits["excluded_seasons"])].copy()

    train_df = eligible_df[eligible_df["season"].isin(season_splits["train_seasons"])].copy()
    val_df = eligible_df[eligible_df["season"].isin(season_splits["val_seasons"])].copy()
    test_df = eligible_df[eligible_df["season"].isin(season_splits["test_seasons"])].copy()

    return train_df, val_df, test_df, season_splits


def evaluate_regression(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)

    return {
        "rmse": mse ** 0.5,
        "mae": mean_absolute_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
    }


def build_scored_predictions_df(df, y_true, y_pred):
    scored_df = df[["milestone_n"]].copy()
    scored_df["actual"] = y_true.to_numpy()
    scored_df["predicted"] = y_pred
    
    return scored_df


def build_milestone_metrics_df(scored_df):
    rows = []

    for milestone_n, group in scored_df.groupby("milestone_n"):
        metrics = evaluate_regression(group["actual"], group["predicted"])

        rows.append({"milestone_n": milestone_n, "rmse": metrics["rmse"], "mae": metrics["mae"], "r2": metrics["r2"]})
        
    return pd.DataFrame(rows).sort_values("milestone_n")


def log_metrics(prefix, metrics):
    for metric_name, metric_value in metrics.items():
        mlflow.log_metric(f"{prefix}_{metric_name}", metric_value)


def log_milestone_metrics(metrics_df):
    for row in metrics_df.itertuples(index=False):
        mlflow.log_metric(f"test_milestone_{row.milestone_n}_rmse", row.rmse)
        mlflow.log_metric(f"test_milestone_{row.milestone_n}_mae", row.mae)
        mlflow.log_metric(f"test_milestone_{row.milestone_n}_r2", row.r2)


def write_feature_columns_artifact(feature_columns):
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / "feature_columns.json"
    output_path.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")
    return output_path


def write_feature_importance_artifact(model, feature_columns):
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / "feature_importance.csv"

    importance_df = pd.DataFrame({"feature": feature_columns, "importance": model.feature_importances_}).sort_values("importance", ascending=False)

    importance_df.to_csv(output_path, index=False)
    return output_path


def write_residuals_artifact(test_df, y_pred):
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / "test_residuals.csv"

    residuals_df = test_df[["nba_id", "bref_id", "season", "milestone_n", "snapshot_date", "label_bpm"]].copy()

    residuals_df["predicted_bpm"] = y_pred
    residuals_df["residual"] = residuals_df["label_bpm"] - residuals_df["predicted_bpm"]
    residuals_df["absolute_error"] = residuals_df["residual"].abs()

    residuals_df.sort_values("absolute_error", ascending=False).to_csv(output_path, index=False)
    return output_path


def write_milestone_metrics_artifact(metrics_df):
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / "test_milestone_metrics.csv"

    metrics_df.to_csv(output_path, index=False)
    return output_path


def train_baseline():
    df = load_feature_snapshots()
    train_df, val_df, test_df, season_splits = split_by_season(df)
    feature_columns = select_feature_columns(df)

    X_train = train_df[feature_columns]
    y_train = train_df[target_column]
    X_val = val_df[feature_columns]
    y_val = val_df[target_column]
    X_test = test_df[feature_columns]
    y_test = test_df[target_column]

    model = XGBRegressor(
        objective="reg:squarederror",
        eval_metric="rmse",
        n_estimators=500,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="bpm-projector") as run:
        mlflow.set_tags(
            {
                "project": "paid-to-play",
                "target": "full_season_bpm",
                "model_family": "xgboost",
                "feature_set_version": feature_set_version,
            }
        )

        mlflow.log_params(
            {
                "model_type": "XGBRegressor",
                "feature_set_version": feature_set_version,
                "train_start_season": training_start_season,
                "train_seasons": ",".join(season_splits["train_seasons"]),
                "val_seasons": ",".join(season_splits["val_seasons"]),
                "test_seasons": ",".join(season_splits["test_seasons"]),
                "excluded_seasons": ",".join(season_splits["excluded_seasons"]),
                "objective": model.objective,
                "eval_metric": model.eval_metric,
                "n_estimators": model.n_estimators,
                "max_depth": model.max_depth,
                "learning_rate": model.learning_rate,
                "subsample": model.subsample,
                "colsample_bytree": model.colsample_bytree,
                "random_state": model.random_state,
            }
        )

        model.fit(
            X_train, 
            y_train, 
            eval_set=[(X_val, y_val)], 
            verbose=False,
        )

        input_example = X_train.head(1).copy()
        output_example = model.predict(input_example)
        signature = infer_signature(input_example, output_example)

        val_predictions = model.predict(X_val)
        test_predictions = model.predict(X_test)

        val_metrics = evaluate_regression(y_val, val_predictions)
        test_metrics = evaluate_regression(y_test, test_predictions)

        scored_df = build_scored_predictions_df(test_df, y_test, test_predictions)
        milestone_metrics_df = build_milestone_metrics_df(scored_df)

        log_metrics("val", val_metrics)
        log_metrics("test", test_metrics)
        log_milestone_metrics(milestone_metrics_df)
        
        feature_columns_path = write_feature_columns_artifact(feature_columns)
        mlflow.log_artifact(str(feature_columns_path))

        feature_importance_path =  write_feature_importance_artifact(model, feature_columns)
        mlflow.log_artifact(str(feature_importance_path))

        residuals_path = write_residuals_artifact(test_df, test_predictions)
        mlflow.log_artifact(str(residuals_path))

        milestone_metrics_path = write_milestone_metrics_artifact(milestone_metrics_df)
        mlflow.log_artifact(str(milestone_metrics_path))

        mlflow.xgboost.log_model(
            xgb_model=model,
            name="model",
            input_example=input_example,
            signature=signature,
            registered_model_name="bpm-projector",
        )
        
        print("Validation metrics:", val_metrics)
        print("Test metrics:", test_metrics)

        return run.info.run_id


if __name__ == "__main__":
    train_baseline()