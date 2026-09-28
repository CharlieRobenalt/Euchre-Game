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
        rules = main.CardRules(kitty_suit)
        trump_count = sum(1 for c in hand if rules.effective_suit(c) == kitty_suit)
        if trump_count >= 3:
            return player_num, kitty_suit
    return None, None


def bot_chooseTrumpNonKitty(self):
    start = 1 if self.dealer == 4 else self.dealer + 1
    turn_order = [(start + i - 1) % 4 + 1 for i in range(4)]
    kitty_suit = self.kittyCard[0]
    available_suits = [s for s in ["H", "D", "C", "S"] if s != kitty_suit]

    for player_num in turn_order:
        hand = self.hands[player_num]
        for suit in available_suits:
            rules = main.CardRules(suit)
            trump_count = sum(1 for c in hand if rules.effective_suit(c) == suit)
            if trump_count >= 3:
                return player_num, suit

    # Stick the dealer
    dealer_hand = self.hands[self.dealer]
    best_suit = max(
        available_suits,
        key=lambda s: sum(1 for c in dealer_hand if main.CardRules(s).effective_suit(c) == s)
    )
    return self.dealer, best_suit


def bot_discardCard(self):
    dealer_hand = self.hands[self.dealer]
    dealer_hand.add(self.kittyCard)
    rules = main.CardRules(self.trump_suit)
    card_to_discard = min(dealer_hand, key=lambda c: rules.card_value(c))
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
            chosen_card = get_random_card(hand, legal_cards, cards_played, rules, self.trump_suit)

        self.played_cards_history.append(chosen_card)
        hand.remove(chosen_card)
        cards_played.append((player_num, chosen_card))

        if led_suit is None:
            led_suit = rules.effective_suit(chosen_card)
            rules.led_suit = led_suit

    winner_player = self.determine_trick_winner(cards_played, rules)
    return winner_player


# ==============================================================================
# 5. SIMULATION CONTROLLER
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
    print(f"Team 2 (Random) Wins: {t2_wins} ({t2_wins / num_games * 100:.1f}%)")


if __name__ == "__main__":
    run_benchmark(num_games=500)