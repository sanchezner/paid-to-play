from __future__ import annotations

import os
from dataclasses import dataclass

import mlflow
from dotenv import load_dotenv
from mlflow.tracking import MlflowClient

load_dotenv()

bpm_model_name = "bpm-projector"
calibration_model_name = "bpm-to-cap-trend"
champion_alias = "champion"
bpm_gate_metric = "test_rmse"


@dataclass(frozen=True)
class PromotionResult:
    model_name: str
    run_id: str
    version: str
    promoted: bool
    reason: str
    new_metric: float=None
    champion_metric: float=None


def get_client(tracking_uri=None):
    uri = tracking_uri or os.getenv("TRACKING_URI")
    mlflow.set_tracking_uri(uri)
    return MlflowClient(tracking_uri=uri)


def get_version_for_run(client, model_name, run_id):
    versions = client.search_model_versions(
        filter_string=f"name='{model_name}' AND run_id='{run_id}'"
    )
    if not versions:
        raise ValueError(f'No {model_name} version registered for run {run_id}')
    return versions[0].version


def get_run_metric(client, run_id, metric_key):
    run = client.get_run(run_id)
    metrics = run.data.metrics
    if metric_key not in metrics:
        available = ", ".join(sorted(metrics))
        raise KeyError(f"Run {run_id} has no metric '{metric_key}'. Available: {available}")
    return metrics[metric_key]


def get_champion_version(client, model_name):
    try:
        return client.get_model_version_by_alias(model_name, champion_alias)
    except mlflow.MlflowException as exc:
        if exc.error_code == "RESOURCE_DOES_NOT_EXIST":
            return None
        raise


def promote_version(client, model_name, version):
    client.set_registered_model_alias(model_name, champion_alias, version)


def gate_bpm_projector(client, run_id):
    new_test_rmse = get_run_metric(client, run_id, bpm_gate_metric)
    version = get_version_for_run(client, bpm_model_name, run_id)

    champion = get_champion_version(client, bpm_model_name)
    if champion is None:
        promote_version(client, bpm_model_name, version)
        return PromotionResult(
            model_name=bpm_model_name,
            run_id=run_id,
            version=version,
            promoted=True,
            reason="no existing champion",
            new_metric=new_test_rmse,
        )

    champion_test_rmse = get_run_metric(client, champion.run_id, bpm_gate_metric)
    if new_test_rmse < champion_test_rmse:
        promote_version(client, bpm_model_name, version)
        return PromotionResult(
            model_name=bpm_model_name,
            run_id=run_id,
            version=version,
            promoted=True,
            reason=f"test_rmse improved {champion_test_rmse:.4f} -> {new_test_rmse:.4f}",
            new_metric=new_test_rmse,
            champion_metric=champion_test_rmse,
        )

    return PromotionResult(
        model_name=bpm_model_name,
        run_id=run_id,
        version=version,
        promoted=False,
        reason=f"test_rmse did not improve ({new_test_rmse:.4f} >= {champion_test_rmse:.4f})",
        new_metric=new_test_rmse,
        champion_metric=champion_test_rmse,
    )


def promote_calibration(client, run_id):
    version = get_version_for_run(client, calibration_model_name, run_id)
    training_rows = get_run_metric(client, run_id, "training_rows")
    promote_version(client, calibration_model_name, version)

    return PromotionResult(
        model_name=calibration_model_name,
        run_id=run_id,
        version=version,
        promoted=True,
        reason=f"annual calibration refresh ({int(training_rows)} training rows)",
        new_metric=training_rows,
    )


def run_promotion_gates(bpm_run_id, calibration_run_id, tracking_uri=None):
    client = get_client(tracking_uri)
    bpm_result = gate_bpm_projector(client, bpm_run_id)
    calibration_result = promote_calibration(client, calibration_run_id)

    for result in (bpm_result, calibration_result):
        status = "promoted" if result.promoted else "skipped"
        print(
            f"{result.model_name} v{result.version} ({status}): {result.reason}"
        )

    return {
        "bpm_projector": bpm_result,
        "calibration": calibration_result,
    }
