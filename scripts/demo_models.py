"""Run synthetic smoke test; NEVER use these numbers as USA headline."""
from pathlib import Path
from ews.models.runner import run_fixture

if __name__ == "__main__":
    table, fold = run_fixture()
    destination = Path("outputs/results/fixture")
    destination.mkdir(parents=True, exist_ok=True)
    table.to_csv(destination / "synthetic_model_metrics.csv", index=False)
    print("SYNTHETIC FIXTURE ONLY — NOT USA OUT-OF-SAMPLE RESULTS")
    print(table[["model", "pr_auc", "roc_auc", "brier"]].to_string(index=False))
    print("Saved:", destination / "synthetic_model_metrics.csv")
