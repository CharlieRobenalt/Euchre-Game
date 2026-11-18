import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

import logger

DATA_FILE = "my_moves_with_trumps.csv"

# ==============================================================================
# 1. LOAD & PREPARE DATA
# ==============================================================================
print(f"Loading data from {DATA_FILE}...")
df = pd.read_csv(DATA_FILE)

FEATURE_COLUMNS = (
    [f"hand_card_{i}" for i in range(24)]
    + ["played_1st", "played_2nd", "played_3rd"]
    + ["partner_played", "partner_card", "partner_winning"]
    + ["trump", "lead_card"]
    + [f"trump_played_{name}" for name in logger.TRUMP_RANK_NAMES]
)

X = df[FEATURE_COLUMNS]
y = df["chosen_card"]

# 80/20 Train-Test Split (stratify on chosen_card to preserve class balance)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print(f"Dataset split: {len(X_train)} training rows | {len(X_test)} out-of-sample test rows.")

# ==============================================================================
# 2. FIT TEMPORARY MODEL (Does NOT overwrite my_ai_model.pkl)
# ==============================================================================
print("Training an RandomForest on the 80% train split...")
eval_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=14,
    min_samples_leaf=4,
    min_samples_split=8,
    max_features="sqrt",
    random_state=42,
    n_jobs=-1
)
eval_model.fit(X_train, y_train)

# ==============================================================================
# 3. EVALUATE OUT-OF-SAMPLE ON 20% TEST SET
# ==============================================================================
print("Generating out-of-sample predictions on unseen test split...")
probs = eval_model.predict_proba(X_test)
classes = eval_model.classes_

top1_all = 0
top1_non_trivial = 0
top2_non_trivial = 0
total_test_turns = len(X_test)
non_trivial_count = 0

for i in range(total_test_turns):
    true_card = y_test.iloc[i]
    row_probs = probs[i]

    # Reconstruct cards physically in hand from one-hot features
    hand_cards = [
        card_id for card_id in range(24) if X_test.iloc[i][f"hand_card_{card_id}"] == 1
    ]

    prob_map = {cls: p for cls, p in zip(classes, row_probs)}

    # Rank cards in hand by model-assigned probability
    ranked_cards = sorted(hand_cards, key=lambda c: prob_map.get(c, -1.0), reverse=True)

    # Raw Top-1 across all turns
    if ranked_cards and ranked_cards[0] == true_card:
        top1_all += 1

    # Filtered evaluation (turns with > 1 card in hand)
    if len(hand_cards) > 1:
        non_trivial_count += 1
        if ranked_cards and ranked_cards[0] == true_card:
            top1_non_trivial += 1
        if ranked_cards and true_card in ranked_cards[:2]:
            top2_non_trivial += 1

# ==============================================================================
# 4. REPORT
# ==============================================================================
print("\n" + "=" * 45)
print("   OUT-OF-SAMPLE (20% HELD-OUT) ACCURACY")
print("=" * 45)
print(f"Total Test Turns:               {total_test_turns}")
print(f"Raw Top-1 Accuracy:             {top1_all / total_test_turns * 100:.2f}%")
print(f"Non-Trivial Turns (Hand > 1):   {non_trivial_count}")
print(f"Filtered Top-1 Accuracy:        {top1_non_trivial / non_trivial_count * 100:.2f}%")
print(f"Filtered Top-2 Accuracy:        {top2_non_trivial / non_trivial_count * 100:.2f}%")
print("=" * 45)