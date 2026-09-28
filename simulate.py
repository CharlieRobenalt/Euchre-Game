import os
import sys
import time
import pickle
import pandas as pd
import random

import main
import logger

# ==============================================================================
# 1. LOAD MODEL & DISABLE FILE LOGGERS
# ==============================================================================
with open("my_ai_model.pkl", "rb") as f:
    ML_MODEL = pickle.load(f)

# Suppress disk/CSV writes by replacing loggers in main with no-ops
noop = lambda *args, **kwargs: None
main.log_move = noop
main.log_bidding_decision = noop
main.log_discard_decision = noop

# Exact feature header order from logger.log_move (excluding 'chosen_card')
FEATURE_COLUMNS = (
    [f"hand_card_{i}" for i in range(24)]
    + ["played_1st", "played_2nd", "played_3rd"]
    + ["partner_played", "partner_card", "partner_winning"]
    + ["trump", "lead_card"]
    + [f"trump_played_{name}" for name in logger.TRUMP_RANK_NAMES]
)


# ==============================================================================
# 2. FEATURE EXTRACTION (Matches logger.py verbatim)
# ==============================================================================
def extract_state_features(player_num, hand, trump_suit, cards_played_this_trick, played_cards_history, rules):
    """Generates the exact 39-feature row matching my_moves_with_trumps.csv."""
    # Trump played vector
    all_played = list(played_cards_history) + [card for _, card in cards_played_this_trick]
    trump_played_vector = logger.get_trump_played_vector(all_played, trump_suit)

    # 1. Hand vector (24)
    hand_vector = [0] * 24
    for card in hand:
        hand_vector[logger.card_to_id(card)] = 1

    # 2. Partner seat
    partner_num = player_num + 2 if player_num <= 2 else player_num - 2

    # 3. Relative slots (3)
    relative_slots = [-1, -1, -1]
    for i, (_, card) in enumerate(cards_played_this_trick):
        relative_slots[i] = logger.card_to_id(card)

    # 4. Partner interaction
    partner_card = next((card for p_num, card in cards_played_this_trick if p_num == partner_num), None)
    partner_played_flag = 1 if partner_card is not None else 0
    partner_card_id = logger.card_to_id(partner_card) if partner_card is not None else -1

    partner_winning_flag = 0
    if partner_card is not None and cards_played_this_trick:
        best_so_far = max(cards_played_this_trick, key=lambda pc: rules.card_value(pc[1]))
        if best_so_far[0] == partner_num:
            partner_winning_flag = 1

    trump_val = logger.SUIT_MAP[trump_suit]
    lead_val = relative_slots[0]

    feature_row = (
        hand_vector
        + relative_slots
        + [partner_played_flag, partner_card_id, partner_winning_flag]
        + [trump_val, lead_val]
        + trump_played_vector
    )

    return pd.DataFrame([feature_row], columns=FEATURE_COLUMNS)


# ==============================================================================
# 3. BOT DECISION ENGINES
# ==============================================================================
def get_ml_model_card(player_num, hand, legal_cards, cards_played, played_cards_history, rules, trump_suit):
    """Uses the trained RandomForest model with legal move filtering."""
    if len(legal_cards) == 1:
        return legal_cards[0]

    # --- PARTNER GUARD ---
    # If your partner is currently holding the highest card on this trick,
    # don't waste high cards or trump: slough your lowest legal card!
    partner_num = player_num + 2 if player_num <= 2 else player_num - 2
    if cards_played:
        best_played = max(cards_played, key=lambda pc: rules.card_value(pc[1]))
        if best_played[0] == partner_num:
            return min(legal_cards, key=lambda c: rules.card_value(c))
    # ---------------------

    # Build input features
    features_df = extract_state_features(
        player_num, hand, trump_suit, cards_played, played_cards_history, rules
    )

    # Get class probabilities
    probs = ML_MODEL.predict_proba(features_df)[0]
    classes = ML_MODEL.classes_  # Array of card_ids (integers 0..23)

    prob_dict = {cls: prob for cls, prob in zip(classes, probs)}

    # Pick the legal card that has the highest model score
    best_card = max(legal_cards, key=lambda c: prob_dict.get(logger.card_to_id(c), -1.0))
    return best_card


def get_heuristic_card(hand, legal_cards, cards_played, rules, trump_suit):
    """Rule-based opponent."""
    if len(legal_cards) == 1:
        return legal_cards[0]

    # Leading
    if not cards_played:
        off_aces = [c for c in legal_cards if c[1] == 14 and rules.effective_suit(c) != trump_suit]
        if off_aces:
            return off_aces[0]
        return min(legal_cards, key=lambda c: rules.card_value(c))

    # Following
    highest_played = max(cards_played, key=lambda x: rules.card_value(x[1]))
    highest_val = rules.card_value(highest_played[1])

    winning_cards = [c for c in legal_cards if rules.card_value(c) > highest_val]
    if winning_cards:
        return min(winning_cards, key=lambda c: rules.card_value(c))

    return min(legal_cards, key=lambda c: rules.card_value(c))


def get_random_card(hand, legal_cards, cards_played, rules, trump_suit):
    """Truly random legal bot opponent."""
    return random.choice(legal_cards)


# ==============================================================================
# 4. OVERRIDE HAND METHODS (Automate Bidding & Play)
# ==============================================================================
def bot_chooseTrumpKitty(self):
    start = 1 if self.dealer == 4 else self.dealer + 1
    turn_order = [(start + i - 1) % 4 + 1 for i in range(4)]
    kitty_suit = self.kittyCard[0]

    for player_num in turn_order:
        hand = self.hands[player_num]
        is_dealer = (player_num == self.dealer)
        partner_num = player_num + 2 if player_num <= 2 else player_num - 2
        partner_dealer = (partner_num == self.dealer)

        # Add kitty card to dealers hand for evaluation
        hand_to_evaluate = set(hand) | {self.kittyCard} if is_dealer else set(hand)

        # Evaluate bidding strength and decide whether to order up the kitty
        if evaluate_bidding_Strength(hand_to_evaluate, self.kittyCard, is_dealer, partner_dealer):
            return player_num, kitty_suit

    return None, None  # No one chooses to order up the kitty




def bot_chooseTrumpNonKitty(self):
    start = 1 if self.dealer == 4 else self.dealer + 1
    turn_order = [(start + i - 1) % 4 + 1 for i in range(4)]
    kitty_suit = self.kittyCard[0]
    available_suits = [s for s in ["H", "D", "C", "S"] if s != kitty_suit]

    for player_num in turn_order:
        hand = self.hands[player_num]
        is_dealer = (player_num == self.dealer)
        partner_num = player_num + 2 if player_num <= 2 else player_num - 2
        partner_dealer = (partner_num == self.dealer)

        for suit in available_suits:
            if evaluate_bidding_Strength(hand, (suit, 0), is_dealer, partner_dealer):
                return player_num, suit


    # Stick the dealer if no one else chooses
    dealer_hand = self.hands[self.dealer]
    best_suit = max(
        available_suits,
        key=lambda s: sum(1 for c in dealer_hand if main.CardRules(s).effective_suit(c) == s)
    )
    return self.dealer, best_suit


def bot_discardCard(self):
    dealer_hand = self.hands[self.dealer]
    dealer_hand.add(self.kittyCard)
    card_to_discard = choose_Smart_discard(dealer_hand, self.trump_suit)
    dealer_hand.remove(card_to_discard)


def bot_playTrick(self):
    rules = main.CardRules(self.trump_suit)
    cards_played = []
    led_suit = None

    turn_order = [(self.leader + i - 1) % 4 + 1 for i in range(4)]

    for player_num in turn_order:
        hand = self.hands[player_num]
        legal_cards = self.get_legal_cards(hand, led_suit, rules)

        # Team 1 (Players 1 & 3): ML Model
        # Team 2 (Players 2 & 4): Heuristic Bot
        if player_num in [1, 3]:
            chosen_card = get_ml_model_card(
                player_num, hand, legal_cards, cards_played, self.played_cards_history, rules, self.trump_suit
            )
        else:
            chosen_card = get_heuristic_card(hand, legal_cards, cards_played, rules, self.trump_suit)

        self.played_cards_history.append(chosen_card)
        hand.remove(chosen_card)
        cards_played.append((player_num, chosen_card))

        if led_suit is None:
            led_suit = rules.effective_suit(chosen_card)
            rules.led_suit = led_suit

    winner_player = self.determine_trick_winner(cards_played, rules)
    return winner_player

# ==============================================================================
# BIDDING & DISCAARD LOGIC
# ==============================================================================
def evaluate_bidding_Strength(hand, kitty_card, isDealer = False, isPartnerDealer = False):
    """Calculates expected trick points instead of just counting raw trumps."""
    rules = main.CardRules(kitty_card[0])
    trumps = [c for c in hand if rules.effective_suit(c) == kitty_card[0]]
    off_cards = [c for c in hand if rules.effective_suit(c) != kitty_card[0]]

    expected_tricks = 0.0

    # Trump Values
    for c in trumps:
        value = rules.card_value(c)
        if value == 100: expected_tricks += 1.0  # Right Bower
        elif value == 99: expected_tricks += 0.9  # Left Bower
        elif value == 64: expected_tricks += 0.75  # Ace of Trump
        elif value >= 62: expected_tricks += 0.45  # King and Queen of Trump
        else: expected_tricks += 0.25  # Other Trump Cards

    off_Aces = [c for c in off_cards if c[1] == 14]
    expected_tricks += 0.5 * len(off_Aces)  # Each off Ace

    if isDealer:
        expected_tricks += 0.35  # Dealer advantage 

    if isPartnerDealer:
        expected_tricks += 0.15  # Partner dealer advantage

    # Threshold for calling it trump
    threshold = 2.2 if (isDealer or isPartnerDealer) else 2.7
    return expected_tricks >= threshold
    

def choose_Smart_discard(hand_with_kitty, trump_suit):
    """Discards to create a void in an off-suit so dealer can trump early."""
    rules = main.CardRules(trump_suit)
    non_trumps = [c for c in hand_with_kitty if rules.effective_suit(c) != trump_suit]

    # If holding 6 trump discard lowest trump
    if not non_trumps:
        return min(hand_with_kitty, key=lambda c: rules.card_value(c))

    # Count the number of cards in each non-trump suit
    suit_counts = {}
    for c in non_trumps:
        suit_counts[c[0]] = suit_counts.get(c[0], 0) + 1

    # Find suits with the one card
    short_suits = [c for c in non_trumps if suit_counts.get(c[0], 0) == 1]
    if short_suits:
        return min(short_suits, key=lambda c: rules.card_value(c))

    # Otherwise, discard the lowest non-trump card
    return min(non_trumps, key=lambda c: rules.card_value(c))


# ==============================================================================
# SIMULATION CONTROLLER
# ==============================================================================
class SuppressOutput:
    """Redirects stdout to /dev/null so prints do not slow down the simulation."""
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def run_benchmark(num_games=500):
    # Patch main.Hand methods
    main.Hand.chooseTrumpKitty = bot_chooseTrumpKitty
    main.Hand.chooseTrumpNonKitty = bot_chooseTrumpNonKitty
    main.Hand.discardCard = bot_discardCard
    main.Hand.playTrick = bot_playTrick

    print(f"Starting headless simulation of {num_games} games...")
    print("Matchup: Team 1 (ML Model) vs Team 2 (Baseline Random)\n")

    start_time = time.time()
    t1_wins = 0
    t2_wins = 0

    with SuppressOutput():
        for i in range(1, num_games + 1):
            game = main.Game()
            game.playGame()
            if game.score[0] >= 10:
                t1_wins += 1
            else:
                t2_wins += 1

    elapsed = time.time() - start_time
    print("--- Benchmark Complete ---")
    print(f"Total Time: {elapsed:.2f}s ({num_games / elapsed:.1f} games/second)")
    print(f"Team 1 (ML Model) Wins:  {t1_wins} ({t1_wins / num_games * 100:.1f}%)")
    print(f"Team 2 (Heuristic) Wins: {t2_wins} ({t2_wins / num_games * 100:.1f}%)")


if __name__ == "__main__":
    run_benchmark(num_games=500)