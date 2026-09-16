import csv
import os

# Map card ranks and suits to consistent integers
SUIT_MAP = {"H": 0, "D": 1, "C": 2, "S": 3}
RANK_MAP = {9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14}

def card_to_id(card):
    """Converts a card tuple like ('H', 11) into a unique integer (0 to 23)."""
    suit, rank = card
    return SUIT_MAP[suit] * 6 + (rank - 9)

def log_move(hand, trump_suit, lead_card, chosen_card, filename="my_moves.csv"):
    """Encodes the current turn and writes it as a row in CSV."""
    # Create a 24-length binary vector representing cards in hand (1 if held, 0 if not)
    hand_vector = [0] * 24
    for card in hand:
        hand_vector[card_to_id(card)] = 1

    trump_val = SUIT_MAP[trump_suit]
    lead_val = card_to_id(lead_card) if lead_card else -1
    label = card_to_id(chosen_card)

    row = hand_vector + [trump_val, lead_val, label]

    write_header = not os.path.exists(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            headers = [f"card_{i}" for i in range(24)] + ["trump", "lead_card", "chosen_card"]
            writer.writerow(headers)
        writer.writerow(row)