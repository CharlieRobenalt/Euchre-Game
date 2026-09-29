import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

import logger

DATA_FILE = "my_moves_with_trumps.csv"
MODEL_FILE = "my_ai_model.pkl"

FEATURE_COLUMNS = (
    [f"hand_card_{i}" for i in range(24)]
    + ["played_1st", "played_2nd", "played_3rd"]
    + ["partner_played", "partner_card", "partner_winning"]
    + ["trump", "lead_card"]
    + [f"trump_played_{name}" for name in logger.TRUMP_RANK_NAMES]
)


def train_clone():
    print(f"Loading {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)

    X = df[FEATURE_COLUMNS]
    y = df["chosen_card"]

    # 1. Quick validation check on 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    eval_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=14,
        min_samples_leaf=4,
        min_samples_split=8,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )
    eval_model.fit(X_train, y_train)
    preds = eval_model.predict(X_test)
    print(f"Out-of-sample raw test accuracy: {accuracy_score(y_test, preds):.2%}")

    # 2. Train the final production model on 100% of available data
    print("Fitting final production model on all 100% of data...")
    final_model = RandomForestClassifier(
        n_estimators=100,          # Drops inference time
        max_depth=18,             # Allows sharper distinction on key cards
        min_samples_leaf=2,       # Keeps sharp leaf outputs while preventing single-sample noise
        min_samples_split=4,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )
    final_model.fit(X, y)

    # 3. Save the full model
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(final_model, f)

    print(f"Production model trained on {len(df)} rows and saved to '{MODEL_FILE}'!")


if __name__ == "__main__":
    train_clone()