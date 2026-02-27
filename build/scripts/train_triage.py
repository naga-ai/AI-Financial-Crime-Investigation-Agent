"""Train the XGBoost triage classifier on the generated alert data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.triage.classifier import train_triage_model


def main() -> None:
    print("=" * 60)
    print("AML Alert Triage Classifier Training")
    print("=" * 60)
    model, metrics = train_triage_model(save=True)
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
