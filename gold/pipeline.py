from gold.features import build_feature_snapshots, validate_feature_snapshots


def build_gold(engine):
    build_feature_snapshots(engine)
    validate_feature_snapshots(engine)
