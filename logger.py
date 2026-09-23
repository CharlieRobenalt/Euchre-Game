import csv
import os

# Map card ranks and suits to consistent integers
SUIT_MAP = {"H": 0, "D": 1, "C": 2, "S": 3}
RANK_MAP = {9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14}
SAME_COLOR = {"H": "D", "D": "H", "C": "S", "S": "C"}
TRUMP_RANK_NAMES = ["right_bower", "left_bower", "A", "K", "Q", "10", "9"]

# Creates True/False vector of which trump cards have been played, in order of rank
def get_trump_played_vector(played_cards, trump_suit):
    left_suit = SAME_COLOR[trump_suit]
    trump_slots = [
        (trump_suit, 11),  # Right Bower
        (left_suit, 11),  # Left Bower
        (trump_suit, 14),  # Ace
        (trump_suit, 13),  # King
        (trump_suit, 12),  # Queen
        (trump_suit, 10),  # 10
        (trump_suit, 9),  # 9
    ]
    played_set = set(played_cards)
    return [1 if card in played_set else 0 for card in trump_slots]

def card_to_id(card):
    """Converts a card tuple like ('H', 11) into a unique integer (0 to 23)."""
    suit, rank = card
    return SUIT_MAP[suit] * 6 + (rank - 9)

# Currently Tracks player's hand, cards played this trick, partner's play, partner's winning status,
# trump suit, lead card, and chosen card.

def log_move(player_num, hand, trump_suit, cards_played_this_trick, played_cards_history, rules, chosen_card, filename="my_moves_with_trumps.csv"):
    """Encodes the current turn and writes it as a row in CSV.
    cards_played_this_trick: list of (player_num, card) tuples, in play order, for this trick so far.
    trump_cards_played: list of trump cards that have been played.
    rules: the CardRules instance for this trick (needed to check who's currently winning)."""

    # Create Trump Played Vector
    all_played_cards = list(played_cards_history) + [
    card for _, card in cards_played_this_trick
    ]
    trump_played_vector = get_trump_played_vector(all_played_cards, trump_suit)

    # 1. Hand — 24-length binary vector
    hand_vector = [0] * 24
    for card in hand:
        hand_vector[card_to_id(card)] = 1

    # 2. Partner's seat number (1&3 are partners, 2&4 are partners)
    partner_num = player_num + 2 if player_num <= 2 else player_num - 2

    # 3. Encode each already-played card by seat position relative to the current player
    #    (1st, 2nd, 3rd played this trick — up to 3 possible before your turn)
    #    Each slot is -1 if that player hasn't gone yet, otherwise the card's id
    relative_slots = [-1, -1, -1]
    for i, (p_num, card) in enumerate(cards_played_this_trick):
        relative_slots[i] = card_to_id(card)

    # 4. Is your partner currently winning the trick, and what did they play?
    partner_card = next((card for p_num, card in cards_played_this_trick if p_num == partner_num), None)
    partner_played_flag = 1 if partner_card is not None else 0
    partner_card_id = card_to_id(partner_card) if partner_card is not None else -1

    partner_winning_flag = 0
    if partner_card is not None and cards_played_this_trick:
        best_so_far = max(cards_played_this_trick, key=lambda pc: rules.card_value(pc[1]))
        if best_so_far[0] == partner_num:
            partner_winning_flag = 1

    trump_val = SUIT_MAP[trump_suit]
    lead_val = relative_slots[0]  # first card played this trick, if any
    label = card_to_id(chosen_card)

    row = (
        hand_vector
        + relative_slots
        + [partner_played_flag, partner_card_id, partner_winning_flag]
        + [trump_val, lead_val] 
        + trump_played_vector
        + [label]
    )

    write_header = not os.path.exists(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            headers = (
                [f"hand_card_{i}" for i in range(24)]
                + ["played_1st", "played_2nd", "played_3rd"]
                + ["partner_played", "partner_card", "partner_winning"]
                + ["trump", "lead_card"]
                + [f"trump_played_{name}" for name in TRUMP_RANK_NAMES]
                + ["chosen_card"]
            )
            writer.writerow(headers)
        writer.writerow(row)

def log_bidding_decision(player_num, hand, kitty_card, dealer_num, bidding_round, turned_down_suit, bid_decision, filename="bidding_decisions.csv"):
    """Encodes the bidding decision and writes it as a row in CSV.
    player_num: the player making the decision (1-4)
    hand: list of card tuples in the player's hand
    kitty_card: Card tuple ('H', 11) or None
    dealer_num: the player who is the dealer (1-4)
    bidding_round: 1 (kitty stage) or 2 (choosing trump stage)
    turned_down_suit: Integer 0-3 (or -1 in Round 1)
    bid_decision: Integer target: 0=H, 1=D, 2=C, 3=S, 5=Pass, 6=Pick Up
    filename="bidding_decisions.csv",
    """

    # 1. Hand — 24-length binary vector
    hand_vector = [0] * 24
    for card in hand:
        hand_vector[card_to_id(card)] = 1

    # 2. Kitty card ID
    kitty_card_id = card_to_id(kitty_card) if kitty_card is not None else -1

    # 3. Relative positions
    is_dealer = 1 if player_num == dealer_num else 0
    partner_num = player_num + 2 if player_num <= 2 else player_num - 2
    is_partner_dealer = 1 if partner_num == dealer_num else 0
    relative_pos = (player_num - dealer_num) % 4

    # Turned down suit value
    turned_down_suit_val = SUIT_MAP[turned_down_suit] if turned_down_suit in ["H", "D", "C", "S"] else turned_down_suit

    # 4. Construct the row
    row = (
        hand_vector
        + [
            kitty_card_id,
            bidding_round,
            turned_down_suit_val,
            relative_pos,
            is_dealer,
            is_partner_dealer,
        ]
        + [bid_decision if bidding_round == 1 else SUIT_MAP[bid_decision] if bid_decision in ["H", "D", "C", "S"] else 5]
    )

    # 5. Write to CSV
    write_header = not os.path.exists(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            headers = (
                [f"hand_card_{i}" for i in range(24)]
                + [
                    "kitty_card",
                    "bidding_round",
                    "turned_down_suit",
                    "relative_pos",
                    "is_dealer",
                    "is_partner_dealer",
                ]
                + ["bid_decision"]  # Target Y
            )
            writer.writerow(headers)
        writer.writerow(row)

def log_discard_decision(hand, kitty_card, discard_decision, filename="discard_decisions.csv"):
    """Encodes the discard decision and writes it as a row in CSV.
    player_num: the player making the decision (1-4)
    hand: list of card tuples in the player's hand
    kitty_card: Card tuple ('H', 11) or None
    dealer_num: the player who is the dealer (1-4)
    discard_decision: Integer target: 0-5 (index of card to discard from hand + kitty)
    filename="discard_decisions.csv",
    """

    # 1. Hand — 24-length binary vector
    hand_vector = [0] * 24
    for card in hand:
        hand_vector[card_to_id(card)] = 1

    # 2. Kitty card ID
    kitty_card_id = card_to_id(kitty_card)
    decision = card_to_id(discard_decision)  # The card that was discarded


    # 3. Construct the row
    row = (
        hand_vector
        + [
            kitty_card_id,
        ]
        + [decision]
    )

    # 4. Write to CSV
    write_header = not os.path.exists(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            headers = (
                [f"hand_card_{i}" for i in range(24)]
                + [
                    "kitty_card",
                ]
                + ["discard_decision"]  # Target Y
            )
            writer.writerow(headers)
        writer.writerow(row)