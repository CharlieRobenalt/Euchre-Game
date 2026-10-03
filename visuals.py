import tkinter as tk
from tkinter import messagebox
import pickle
import pandas as pd
import random

# Engine & Logger imports from your project
import main
from main import CardRules
import logger

# ==============================================================================
# 1. LOAD MODEL & FEATURE DEFINITIONS
# ==============================================================================
with open("my_ai_model.pkl", "rb") as f:
    ML_MODEL = pickle.load(f)

FEATURE_COLUMNS = (
    [f"hand_card_{i}" for i in range(24)]
    + ["played_1st", "played_2nd", "played_3rd"]
    + ["partner_played", "partner_card", "partner_winning"]
    + ["trump", "lead_card"]
    + [f"trump_played_{name}" for name in logger.TRUMP_RANK_NAMES]
)

SUIT_SYMBOLS = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
RANK_NAMES = {9: "9", 10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"}

def format_card(card):
    suit, rank = card
    return f"{RANK_NAMES[rank]}{SUIT_SYMBOLS[suit]}"

def card_color(card):
    return "#CC0000" if card[0] in ["H", "D"] else "#111111"


# ==============================================================================
# 2. BOT DECISION & FEATURE LOGIC
# ==============================================================================
def extract_state_features(player_num, hand, trump_suit, cards_played_this_trick, played_cards_history, rules):
    all_played = list(played_cards_history) + [card for _, card in cards_played_this_trick]
    trump_played_vector = logger.get_trump_played_vector(all_played, trump_suit)

    hand_vector = [0] * 24
    for card in hand:
        hand_vector[logger.card_to_id(card)] = 1

    partner_num = player_num + 2 if player_num <= 2 else player_num - 2

    relative_slots = [-1, -1, -1]
    for i, (_, card) in enumerate(cards_played_this_trick):
        relative_slots[i] = logger.card_to_id(card)

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


def get_ml_model_card(player_num, hand, legal_cards, cards_played, played_cards_history, rules, trump_suit):
    if len(legal_cards) == 1:
        return legal_cards[0]

    partner_num = player_num + 2 if player_num <= 2 else player_num - 2
    if cards_played:
        best_played = max(cards_played, key=lambda pc: rules.card_value(pc[1]))
        if best_played[0] == partner_num:
            return min(legal_cards, key=lambda c: rules.card_value(c))

    features_df = extract_state_features(
        player_num, hand, trump_suit, cards_played, played_cards_history, rules
    )

    probs = ML_MODEL.predict_proba(features_df)[0]
    classes = ML_MODEL.classes_
    prob_dict = {cls: prob for cls, prob in zip(classes, probs)}

    return max(legal_cards, key=lambda c: prob_dict.get(logger.card_to_id(c), -1.0))


def get_heuristic_card(hand, legal_cards, cards_played, rules, trump_suit):
    if len(legal_cards) == 1:
        return legal_cards[0]

    if not cards_played:
        off_aces = [c for c in legal_cards if c[1] == 14 and rules.effective_suit(c) != trump_suit]
        if off_aces:
            return off_aces[0]
        return min(legal_cards, key=lambda c: rules.card_value(c))

    highest_played = max(cards_played, key=lambda x: rules.card_value(x[1]))
    highest_val = rules.card_value(highest_played[1])

    winning_cards = [c for c in legal_cards if rules.card_value(c) > highest_val]
    if winning_cards:
        return min(winning_cards, key=lambda c: rules.card_value(c))

    return min(legal_cards, key=lambda c: rules.card_value(c))


def evaluate_bidding_Strength(hand, kitty_card, isDealer=False, isPartnerDealer=False):
    trump_suit = kitty_card[0]
    rules = CardRules(trump_suit)
    
    trumps = [c for c in hand if rules.effective_suit(c) == trump_suit]
    off_cards = [c for c in hand if rules.effective_suit(c) != trump_suit]

    expected_tricks = 0.0
    for c in trumps:
        val = rules.card_value(c)
        if val == 100:    expected_tricks += 1.10
        elif val == 99:   expected_tricks += 0.95
        elif val == 64:   expected_tricks += 0.75
        elif val >= 62:   expected_tricks += 0.45
        else:             expected_tricks += 0.20

    off_aces = [c for c in off_cards if c[1] == 14]
    expected_tricks += len(off_aces) * 0.60

    off_suit_counts = {}
    for c in off_cards:
        s = rules.effective_suit(c)
        off_suit_counts[s] = off_suit_counts.get(s, 0) + 1

    singletons = sum(1 for cnt in off_suit_counts.values() if cnt == 1)
    if singletons >= 1:
        expected_tricks += 0.20

    if isDealer:
        expected_tricks += 0.30

    if isPartnerDealer:
        threshold = 2.30
    elif isDealer:
        threshold = 2.85
    else:
        threshold = 3.15

    return expected_tricks >= threshold


def choose_Smart_discard(hand_with_kitty, trump_suit):
    rules = CardRules(trump_suit)
    non_trumps = [c for c in hand_with_kitty if rules.effective_suit(c) != trump_suit]

    if not non_trumps:
        return min(hand_with_kitty, key=lambda c: rules.card_value(c))

    suit_counts = {}
    for c in non_trumps:
        suit_counts[c[0]] = suit_counts.get(c[0], 0) + 1

    short_suits = [c for c in non_trumps if suit_counts.get(c[0], 0) == 1]
    if short_suits:
        return min(short_suits, key=lambda c: rules.card_value(c))

    return min(non_trumps, key=lambda c: rules.card_value(c))


# ==============================================================================
# 3. GRAPHICAL USER INTERFACE
# ==============================================================================
class EuchreGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Euchre - ML Partner & Heuristic Opponents")
        self.root.geometry("900x740")
        self.root.configure(bg="#1E6B37")

        self.dealer = 1
        self.score = [0, 0]
        self.is_discarding = False
        self.reset_hand_state()

        self.setup_ui()
        self.start_new_hand()

    def reset_hand_state(self):
        suits = ["H", "D", "C", "S"]
        ranks = [9, 10, 11, 12, 13, 14]
        self.deck = [(s, r) for s in suits for r in ranks]
        random.shuffle(self.deck)

        self.hands = {p: set(self.deck[i*5:(i+1)*5]) for i, p in enumerate(range(1, 5))}
        self.kitty = self.deck[20]
        self.trump_suit = None
        self.rules = None
        self.decision_maker = None
        self.tricks_won = [0, 0]
        self.current_trick = []
        self.played_cards_history = []
        self.leader = 1 if self.dealer == 4 else self.dealer + 1
        self.turn_order = []
        self.current_player = None
        self.is_discarding = False

    def setup_ui(self):
        # Top Scoreboard
        self.top_bar = tk.Frame(self.root, bg="#144C27", pady=8)
        self.top_bar.pack(fill="x")

        self.score_label = tk.Label(
            self.top_bar, text="", font=("Arial", 12, "bold"), fg="#FFD700", bg="#144C27"
        )
        self.score_label.pack(side="left", padx=20)

        self.trump_label = tk.Label(
            self.top_bar, text="", font=("Arial", 12, "bold"), fg="white", bg="#144C27"
        )
        self.trump_label.pack(side="right", padx=20)

        # Center Board
        self.table = tk.Frame(self.root, bg="#1E6B37")
        self.table.pack(expand=True, fill="both")

        # Partner (Player 3 - ML Agent)
        self.p3_label = tk.Label(
            self.table, text="Partner (P3 - ML Bot)\n[ 5 Cards ]",
            font=("Arial", 11, "bold"), fg="#88E0EF", bg="#1E6B37"
        )
        self.p3_label.pack(side="top", pady=10)

        # Middle Felt
        mid_row = tk.Frame(self.table, bg="#1E6B37")
        mid_row.pack(expand=True, fill="x", padx=40)

        self.p2_label = tk.Label(
            mid_row, text="West (P2 - Heuristic)\n[ 5 Cards ]",
            font=("Arial", 11), fg="white", bg="#1E6B37"
        )
        self.p2_label.pack(side="left")

        self.center_box = tk.Label(
            mid_row, text="", font=("Arial", 13), fg="white", bg="#144C27",
            width=34, height=9, relief="ridge", bd=3
        )
        self.center_box.pack(side="left", expand=True)

        self.p4_label = tk.Label(
            mid_row, text="East (P4 - Heuristic)\n[ 5 Cards ]",
            font=("Arial", 11), fg="white", bg="#1E6B37"
        )
        self.p4_label.pack(side="right")

        # In-GUI Action / Bidding Panel (Directly above player cards)
        self.action_panel = tk.Frame(self.table, bg="#1E6B37", height=45)
        self.action_panel.pack(side="bottom", pady=4)

        # Status Announcer
        self.status_label = tk.Label(
            self.table, text="", font=("Arial", 12, "italic"), fg="#E0FFE0", bg="#1E6B37"
        )
        self.status_label.pack(side="bottom", pady=4)

        # Player Hand Frame (South - You)
        self.hand_frame = tk.Frame(self.root, bg="#1E6B37")
        self.hand_frame.pack(side="bottom", pady=15)

    def clear_action_panel(self):
        for widget in self.action_panel.winfo_children():
            widget.destroy()

    def refresh_screen(self):
        dealer_str = "You (P1)" if self.dealer == 1 else f"P{self.dealer}"
        self.score_label.config(
            text=f"Team 1 (You & ML Bot): {self.score[0]}  |  Team 2 (Heuristics): {self.score[1]}  (Dealer: {dealer_str})"
        )
        
        trump_str = f"Trump: {SUIT_SYMBOLS.get(self.trump_suit, '')} {self.trump_suit}" if self.trump_suit else "Trump: Deciding..."
        self.trump_label.config(text=trump_str)

        self.p2_label.config(text=f"West (P2 - Heuristic)\n[ {len(self.hands[2])} Cards ]")
        self.p3_label.config(text=f"Partner (P3 - ML Bot)\n[ {len(self.hands[3])} Cards ]")
        self.p4_label.config(text=f"East (P4 - Heuristic)\n[ {len(self.hands[4])} Cards ]")

        if self.current_trick:
            lines = ["Current Trick:"]
            for p, c in self.current_trick:
                p_name = "You" if p == 1 else ("Partner (ML)" if p == 3 else f"Player {p}")
                lines.append(f"{p_name}: {format_card(c)}")
            self.center_box.config(text="\n".join(lines))

        # Re-render Human Hand
        for w in self.hand_frame.winfo_children():
            w.destroy()

        my_cards = sorted(list(self.hands[1]), key=lambda c: (c[0], c[1]))
        is_my_turn = (self.current_player == 1)

        legal_cards = []
        if self.is_discarding:
            legal_cards = my_cards
        elif is_my_turn and self.rules:
            led_suit = self.rules.led_suit
            if led_suit is None:
                legal_cards = my_cards
            else:
                matching = [c for c in my_cards if self.rules.effective_suit(c) == led_suit]
                legal_cards = matching if matching else my_cards

        for card in my_cards:
            can_click = (self.is_discarding) or (is_my_turn and (card in legal_cards))
            
            cmd = (lambda drop=card: self.resolve_discard(drop)) if self.is_discarding else (lambda c=card: self.human_play_card(c))

            btn = tk.Button(
                self.hand_frame,
                text=format_card(card),
                font=("Arial", 16, "bold"),
                fg=card_color(card),
                bg="#FFFFFF" if can_click else "#D0D0D0",
                width=5, height=3, relief="raised", bd=3,
                state="normal" if can_click else "disabled",
                command=cmd
            )
            btn.pack(side="left", padx=6)

    # --- In-GUI Bidding Flow ---
    def start_new_hand(self):
        self.reset_hand_state()
        self.clear_action_panel()
        self.center_box.config(text=f"Kitty Card:\n\n{format_card(self.kitty)}")
        self.status_label.config(text="Bidding Round 1: Deciding on kitty...")
        self.refresh_screen()

        self.bidding_order = []
        curr = 1 if self.dealer == 4 else self.dealer + 1
        for _ in range(4):
            self.bidding_order.append(curr)
            curr = 1 if curr == 4 else curr + 1

        self.root.after(800, self.step_kitty_bidding)

    def step_kitty_bidding(self):
        self.clear_action_panel()
        if not self.bidding_order:
            self.status_label.config(text="All passed kitty. Round 2: Calling any suit...")
            self.center_box.config(text=f"Kitty Turned Down:\n\n{format_card(self.kitty)}")
            self.root.after(1000, self.start_non_kitty_bidding)
            return

        p = self.bidding_order.pop(0)
        is_dealer = (p == self.dealer)
        partner_num = p + 2 if p <= 2 else p - 2
        partner_dealer = (partner_num == self.dealer)

        if p == 1:
            # Human choice directly on the board
            order_label = "Pick It Up" if is_dealer else f"Order Up P{self.dealer}"
            self.status_label.config(text=f"Your turn: Order up {format_card(self.kitty)} or Pass?")
            
            btn_pick = tk.Button(
                self.action_panel, text=f"✔ {order_label}", font=("Arial", 12, "bold"),
                bg="#4CAF50", fg="black", padx=12, pady=3,
                command=lambda: self.on_human_kitty_choice(True)
            )
            btn_pick.pack(side="left", padx=10)

            btn_pass = tk.Button(
                self.action_panel, text="✖ Pass", font=("Arial", 12, "bold"),
                bg="#E57373", fg="black", padx=12, pady=3,
                command=lambda: self.on_human_kitty_choice(False)
            )
            btn_pass.pack(side="left", padx=10)
        else:
            hand_eval = set(self.hands[p]) | {self.kitty} if is_dealer else set(self.hands[p])
            if evaluate_bidding_Strength(hand_eval, self.kitty, is_dealer, partner_dealer):
                p_desc = "Partner (ML)" if p == 3 else f"Player {p}"
                self.status_label.config(text=f"{p_desc} ordered up {format_card(self.kitty)}!")
                self.set_trump(maker=p, suit=self.kitty[0], is_kitty=True)
            else:
                p_desc = "Partner (ML)" if p == 3 else f"Player {p}"
                self.status_label.config(text=f"{p_desc} passed.")
                self.root.after(600, self.step_kitty_bidding)

    def on_human_kitty_choice(self, chose_pick):
        self.clear_action_panel()
        if chose_pick:
            self.set_trump(maker=1, suit=self.kitty[0], is_kitty=True)
        else:
            self.status_label.config(text="You passed on the kitty.")
            self.root.after(600, self.step_kitty_bidding)

    def start_non_kitty_bidding(self):
        self.bidding_order = []
        curr = 1 if self.dealer == 4 else self.dealer + 1
        for _ in range(4):
            self.bidding_order.append(curr)
            curr = 1 if curr == 4 else curr + 1

        self.step_non_kitty_bidding()

    def step_non_kitty_bidding(self):
        self.clear_action_panel()
        p = self.bidding_order.pop(0)
        valid_suits = [s for s in ["H", "D", "C", "S"] if s != self.kitty[0]]
        is_dealer = (p == self.dealer)
        partner_num = p + 2 if p <= 2 else p - 2
        partner_dealer = (partner_num == self.dealer)

        if p == 1:
            must_call = is_dealer  # Stick the dealer
            self.status_label.config(
                text="You are stuck dealer - MUST call trump!" if must_call else "Your turn: Call a trump suit or Pass."
            )

            # Suit Selection Buttons on the GUI
            suit_names = {"H": "Hearts", "D": "Diamonds", "C": "Clubs", "S": "Spades"}
            for s in valid_suits:
                btn_color = "#CC0000" if s in ["H", "D"] else "#000000"
                btn_suit = tk.Button(
                    self.action_panel, text=f"{SUIT_SYMBOLS[s]} {suit_names[s]}",
                    font=("Arial", 11, "bold"), fg=btn_color, bg="white", padx=8, pady=3,
                    command=lambda chosen=s: self.on_human_call_suit(chosen)
                )
                btn_suit.pack(side="left", padx=5)

            if not must_call:
                btn_pass = tk.Button(
                    self.action_panel, text="✖ Pass", font=("Arial", 11, "bold"),
                    bg="#E57373", fg="black", padx=10, pady=3,
                    command=self.on_human_pass_non_kitty
                )
                btn_pass.pack(side="left", padx=8)
        else:
            called_suit = None
            for s in valid_suits:
                if evaluate_bidding_Strength(self.hands[p], (s, 0), is_dealer, partner_dealer):
                    called_suit = s
                    break

            if called_suit is None and is_dealer:
                called_suit = max(
                    valid_suits,
                    key=lambda s: sum(1 for c in self.hands[p] if CardRules(s).effective_suit(c) == s)
                )

            if called_suit:
                p_desc = "Partner (ML)" if p == 3 else f"Player {p}"
                self.status_label.config(text=f"{p_desc} called {called_suit} as Trump!")
                self.set_trump(maker=p, suit=called_suit, is_kitty=False)
            else:
                p_desc = "Partner (ML)" if p == 3 else f"Player {p}"
                self.status_label.config(text=f"{p_desc} passed.")
                self.root.after(600, self.step_non_kitty_bidding)

    def on_human_call_suit(self, suit):
        self.clear_action_panel()
        self.set_trump(maker=1, suit=suit, is_kitty=False)

    def on_human_pass_non_kitty(self):
        self.clear_action_panel()
        self.status_label.config(text="You passed.")
        self.root.after(600, self.step_non_kitty_bidding)

    def set_trump(self, maker, suit, is_kitty):
        self.clear_action_panel()
        self.decision_maker = maker
        self.trump_suit = suit
        self.rules = CardRules(self.trump_suit)

        if is_kitty:
            self.hands[self.dealer].add(self.kitty)
            if self.dealer == 1:
                self.prompt_human_discard()
                return
            else:
                discard = choose_Smart_discard(self.hands[self.dealer], self.trump_suit)
                self.hands[self.dealer].remove(discard)

        self.root.after(1000, self.start_trick_phase)

    def prompt_human_discard(self):
        self.is_discarding = True
        self.status_label.config(
            text=f"You picked up {format_card(self.kitty)}. Click any card from your hand below to discard it."
        )
        self.refresh_screen()

    def resolve_discard(self, card):
        self.is_discarding = False
        self.hands[1].remove(card)
        self.status_label.config(text=f"Discarded {format_card(card)}.")
        self.refresh_screen()
        self.root.after(800, self.start_trick_phase)

    # --- Trick Play Flow ---
    def start_trick_phase(self):
        self.clear_action_panel()
        self.current_trick = []
        self.rules.led_suit = None

        self.turn_order = []
        curr = self.leader
        for _ in range(4):
            self.turn_order.append(curr)
            curr = 1 if curr == 4 else curr + 1

        self.play_next_in_trick()

    def play_next_in_trick(self):
        if not self.turn_order:
            self.root.after(1200, self.resolve_trick)
            return

        self.current_player = self.turn_order.pop(0)
        self.refresh_screen()

        if self.current_player == 1:
            self.status_label.config(text="Your turn! Click a highlighted card.")
        else:
            p_desc = "Partner (ML Bot)" if self.current_player == 3 else f"Player {self.current_player}"
            self.status_label.config(text=f"{p_desc} is thinking...")
            self.root.after(700, self.execute_bot_play)

    def human_play_card(self, card):
        self.hands[1].remove(card)
        self.current_trick.append((1, card))
        self.played_cards_history.append(card)

        if self.rules.led_suit is None:
            self.rules.led_suit = self.rules.effective_suit(card)

        self.current_player = None
        self.refresh_screen()
        self.play_next_in_trick()

    def execute_bot_play(self):
        p = self.current_player
        hand = self.hands[p]

        if self.rules.led_suit is None:
            legal_cards = list(hand)
        else:
            matching = [c for c in hand if self.rules.effective_suit(c) == self.rules.led_suit]
            legal_cards = matching if matching else list(hand)

        if p == 3:
            chosen_card = get_ml_model_card(
                player_num=3,
                hand=hand,
                legal_cards=legal_cards,
                cards_played=self.current_trick,
                played_cards_history=self.played_cards_history,
                rules=self.rules,
                trump_suit=self.trump_suit
            )
        else:
            chosen_card = get_heuristic_card(
                hand=hand,
                legal_cards=legal_cards,
                cards_played=self.current_trick,
                rules=self.rules,
                trump_suit=self.trump_suit
            )

        hand.remove(chosen_card)
        self.current_trick.append((p, chosen_card))
        self.played_cards_history.append(chosen_card)

        if self.rules.led_suit is None:
            self.rules.led_suit = self.rules.effective_suit(chosen_card)

        self.refresh_screen()
        self.play_next_in_trick()

    def resolve_trick(self):
        winning_card = None
        winning_player = None

        for p, card in self.current_trick:
            if winning_card is None or self.rules.card_value(card) > self.rules.card_value(winning_card):
                winning_card = card
                winning_player = p

        winner_name = "You" if winning_player == 1 else ("Partner (ML Bot)" if winning_player == 3 else f"Player {winning_player}")
        self.status_label.config(text=f"{winner_name} won the trick with {format_card(winning_card)}!")

        if winning_player in [1, 3]:
            self.tricks_won[0] += 1
        else:
            self.tricks_won[1] += 1

        self.leader = winning_player

        if len(self.hands[1]) == 0:
            self.root.after(1500, self.resolve_hand_score)
        else:
            self.root.after(1500, self.start_trick_phase)

    def resolve_hand_score(self):
        tw = self.tricks_won
        pts = [0, 0]
        if self.decision_maker in [1, 3]:
            if tw[0] in [3, 4]: pts = [1, 0]
            elif tw[0] == 5:    pts = [2, 0]
            else:               pts = [0, 2]
        else:
            if tw[1] in [3, 4]: pts = [0, 1]
            elif tw[1] == 5:    pts = [0, 2]
            else:               pts = [2, 0]

        self.score[0] += pts[0]
        self.score[1] += pts[1]

        summary = f"Hand Over!\nTricks Won — Team 1 (You & ML): {tw[0]}, Team 2: {tw[1]}\n"
        summary += f"Points Added — Team 1: +{pts[0]}, Team 2: +{pts[1]}"
        messagebox.showinfo("Hand Summary", summary)

        if max(self.score) >= 10:
            winner = "Team 1 (You & Partner)" if self.score[0] >= 10 else "Team 2 (Opponents)"
            messagebox.showinfo("Game Over", f"{winner} wins the game!")
            self.root.destroy()
        else:
            self.dealer = 1 if self.dealer == 4 else self.dealer + 1
            self.start_new_hand()


if __name__ == "__main__":
    root = tk.Tk()
    app = EuchreGUI(root)
    root.mainloop()