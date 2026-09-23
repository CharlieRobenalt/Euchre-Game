import csv

OLD_FILE = "my_moves.csv"
NEW_FILE = "my_moves_with_trumps.csv"

# Map suits and ranks back to card IDs
SUIT_MAP = {"H": 0, "D": 1, "C": 2, "S": 3}
INT_TO_SUIT = {0: "H", 1: "D", 2: "C", 3: "S"}
SAME_COLOR = {"H": "D", "D": "H", "C": "S", "S": "C"}

TRUMP_NAMES = [
    "trump_played_right_bower",
    "trump_played_left_bower",
    "trump_played_A",
    "trump_played_K",
    "trump_played_Q",
    "trump_played_10",
    "trump_played_9",
]


def card_to_id(suit, rank):
    """Converts a card suit and rank into an integer ID (0 to 23)."""
    return SUIT_MAP[suit] * 6 + (rank - 9)


def get_trump_card_ids(trump_suit_str):
    """Returns the 7 card IDs for trump cards in order: [Right, Left, A, K, Q, 10, 9]."""
    left_suit = SAME_COLOR[trump_suit_str]
    trump_slots = [
        (trump_suit_str, 11),  # Right Bower
        (left_suit, 11),  # Left Bower
        (trump_suit_str, 14),  # Ace
        (trump_suit_str, 13),  # King
        (trump_suit_str, 12),  # Queen
        (trump_suit_str, 10),  # 10
        (trump_suit_str, 9),  # 9
    ]
    return [card_to_id(suit, rank) for suit, rank in trump_slots]


def backfill_trump_history(input_path, output_path):
    with (
        open(input_path, mode="r", newline="") as infile,
        open(output_path, mode="w", newline="") as outfile,
    ):
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        headers = next(reader)
        # Position: insert the 7 trump columns right before 'chosen_card'
        new_headers = headers[:-1] + TRUMP_NAMES + [headers[-1]]
        writer.writerow(new_headers)

        hand_cards_so_far = set()
        prev_hand_size = None

        for row in reader:
            if not row:
                continue

            # Hand cards are columns 0 through 23
            hand_cards = [int(val) for val in row[:24]]
            hand_size = sum(hand_cards)

            # Columns relative to the end:
            # -3: trump, -2: lead_card, -1: chosen_card
            trump_val = int(row[-3])
            trump_str = INT_TO_SUIT[trump_val]

            # Reset whenever hand size returns to 5 from a smaller hand size
            # (or at the very start of the file)
            if hand_size == 5 and (
                prev_hand_size is None or prev_hand_size < 5
            ):
                hand_cards_so_far.clear()

            prev_hand_size = hand_size

            # Cards played earlier this trick (indices 24, 25, 26)
            played_slots = [int(row[24]), int(row[25]), int(row[26])]
            for card_id in played_slots:
                if card_id != -1:
                    hand_cards_so_far.add(card_id)

            # Build the 7-bit binary vector for the current decision point
            trump_card_ids = get_trump_card_ids(trump_str)
            trump_vector = [
                1 if cid in hand_cards_so_far else 0 for cid in trump_card_ids
            ]

            # Insert the trump vector right before chosen_card
            new_row = row[:-1] + trump_vector + [row[-1]]
            writer.writerow(new_row)

            # Record chosen card so subsequent turns in this deal know it has been played
            chosen_card_id = int(row[-1])
            hand_cards_so_far.add(chosen_card_id)


if __name__ == "__main__":
    backfill_trump_history(OLD_FILE, NEW_FILE)
    print(f"Migration complete! Output written to: {NEW_FILE}")