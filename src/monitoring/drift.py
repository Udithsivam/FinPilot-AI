"""Feature drift detection: reference (training) distribution vs. current
production/inference distribution, using the Kolmogorov-Smirnov test for
numeric features.

Thresholds are configured in one place (DRIFT_THRESHOLDS below), not
scattered through calling code, per the "configure thresholds in one
place" requirement.
"""

from scipy.stats import ks_2samp

MIN_SAMPLES = 10

# KS statistic thresholds. The KS statistic is the max distance between
# the two samples' empirical CDFs, in [0, 1] — 0 means identical
# distributions, larger means more divergence. These cutoffs are a
# reasonable, commonly-used starting point (not derived from this
# project's own historical drift incidents, since none exist yet); they
# are deliberately centralized here so they can be tuned in one place
# rather than hunted down across every caller.
DRIFT_THRESHOLDS = {
    "warning": 0.15,
    "drift_detected": 0.3,
}


def _status_for_statistic(statistic: float) -> str:
    if statistic >= DRIFT_THRESHOLDS["drift_detected"]:
        return "drift_detected"
    if statistic >= DRIFT_THRESHOLDS["warning"]:
        return "warning"
    return "stable"


def detect_feature_drift(feature_name: str, reference: list[float], current: list[float]) -> dict:
    """Compare `reference` (training-time distribution) against `current`
    (recent production/inference values) for one numeric feature.

    Reports "insufficient_data" rather than a fabricated statistic when
    either sample is too small to say anything meaningful.
    """
    base = {"feature": feature_name, "metric": "kolmogorov_smirnov"}

    if len(reference) < MIN_SAMPLES or len(current) < MIN_SAMPLES:
        return {
            **base,
            "value": None,
            "threshold": DRIFT_THRESHOLDS["warning"],
            "status": "insufficient_data",
            "reference_size": len(reference),
            "current_size": len(current),
        }

    result = ks_2samp(reference, current)
    statistic = float(result.statistic)

    return {
        **base,
        "value": round(statistic, 4),
        "threshold": DRIFT_THRESHOLDS["warning"],
        "status": _status_for_statistic(statistic),
        "reference_size": len(reference),
        "current_size": len(current),
    }


def detect_drift_for_features(reference_by_feature: dict[str, list[float]], current_by_feature: dict[str, list[float]]) -> list[dict]:
    results = []
    for feature_name, reference_values in reference_by_feature.items():
        current_values = current_by_feature.get(feature_name, [])
        results.append(detect_feature_drift(feature_name, reference_values, current_values))
    return results
