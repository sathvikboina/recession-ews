
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier


MODEL_NAMES = (
    "logistic",
    "elastic_net",
    "random_forest",
    "xgboost",
    "svm",
    "mlp",
)


def create_model(name: str, seed: int = 42):
    """Create an unfitted model with a common interface."""

    if name == "logistic":
        return LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=seed,
        )

    if name == "elastic_net":
        return LogisticRegression(
            penalty="elasticnet",
            solver="saga",
            l1_ratio=0.5,
            max_iter=3000,
            class_weight="balanced",
            random_state=seed,
        )

    if name == "random_forest":
        return RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=seed,
        )

    if name == "xgboost":
        return XGBClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=seed,
            n_jobs=1,
        )

    if name == "svm":
        return SVC(
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=seed,
        )

    if name == "mlp":
        return MLPClassifier(
            hidden_layer_sizes=(32, 16),
            max_iter=500,
            random_state=seed,
        )

    raise ValueError(f"Unknown model: {name}")
