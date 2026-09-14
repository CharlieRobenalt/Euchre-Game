import random

#Sets rules for Card values and suits, including left bower handling
class CardRules:
    SUITS = ["H", "D", "C", "S"]
    SameColor = {"H": "D", "D": "H", "C": "S", "S": "C"}

    # Card Constructor
    def __init__(self, trump_suit, led_suit = None):
        self.trump_suit = trump_suit
        self.left_bower_suit = self.SameColor[trump_suit]
        self.led_suit = led_suit 

    # Returns the suit the card counts as (handles left bower)
    def effective_suit(self, card):
        suit, rank = card
        if suit == self.left_bower_suit and rank == 11:
            return self.trump_suit
        return suit

    def card_value(self, card):
        suit, rank = card
        eff_suit = self.effective_suit(card)

        if eff_suit == self.trump_suit:
            if rank == 11 and suit == self.trump_suit:
                return 100  # Right Bower allways wins
            elif rank == 11 and suit == self.left_bower_suit:
                return 99  # Left Bower only loses to right bower
            else:
                return rank + 50  # Regular trump cards: rank (9-14) + 50, always outranks non-trump cards
        elif suit == self.led_suit:
            return rank  # Non-trump cards of the led suit are ranked normally
        else:   
            return -1  # Non-trump cards of a different suit are ranked lowest and can't win the trick

def main():
    print("Let's play Euchre!")
    dealer = 1
    score = [0, 0]  # Team 1 and Team 2 scores

    deck = resetDeck()
    player1_hand = dealHand(deck)
    player2_hand = dealHand(deck)
    player3_hand = dealHand(deck)
    player4_hand = dealHand(deck)

    kittyCard = deck.pop()  # The top card of the remaining deck is the kitty card
    print("Kitty Card: " + str(kittyCard))

    decisionMaker, suit = chooseTrumpKitty(kittyCard, dealer, player1_hand, player2_hand, player3_hand, player4_hand)

    if decisionMaker is None:
        maker, trump_suit = chooseTrumpNontKitty(kittyCard, dealer, player1_hand, player2_hand, player3_hand, player4_hand)

    if decisionMaker is None:
        print("Everyone passed both rounds! Redeal needed.")
    else:
        print(f"Player {maker} called the trump suit {trump_suit}.")

def resetDeck():
    #Create and shuffle a euchre deck of 24 cards
    suits = ["H", "D", "C", "S"]
    ranks = [9, 10, 11, 12, 13, 14]
    deck = [(suit, rank) for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

def dealHand(deck):
    #deal the player 5 cards
    hand = set()
    for _ in range(5):
        card = deck.pop()
        hand.add(card)
    return hand

def chooseTrumpKitty(kittyCard, dealer, player1_hand, player2_hand, player3_hand, player4_hand):
    print ("kitty card is: " + str(kittyCard))

    hands = {
        1: player1_hand,
        2: player2_hand,
        3: player3_hand,
        4: player4_hand,
    }    
    # Figure out who starts (player after the dealer, wrapping 4 -> 1)
    start = 1 if dealer == 4 else dealer + 1

    # Build turn order starting from that player, wrapping around
    turn_order = []
    current = start
    for _ in range(4):
        turn_order.append(current)
        current = 1 if current == 4 else current + 1
        
    for player_num in turn_order:
        name = f"Player {player_num}" + (" (dealer)" if player_num == dealer else "")
        hand = hands[player_num]
        print(f"{name}'s turn. Your hand is {hand}")

        while True:
            choice = input(f"{name}, do you want to pick it up or pass? (pick/pass): ").lower()
            if choice in ["pick", "pass"]:
                break
            print("Invalid choice, please type 'pick' or 'pass'.")

        if choice == "pick":
            print(f"{name} says pick it up! Player {dealer} picks up the card, making {kittyCard[0]} the trump suit.")
            return player_num, kittyCard[0]
        else:
            print(f"{name} passed.")

    print("Everyone passed! No trump chosen this round.")
    return None, None  

def chooseTrumpNontKitty(kittyCard, dealer, player1_hand, player2_hand, player3_hand, player4_hand):
    hands = {
        1: player1_hand,
        2: player2_hand,
        3: player3_hand,
        4: player4_hand,
    }    
    # Figure out who starts (player after the dealer, wrapping 4 -> 1)
    start = 1 if dealer == 4 else dealer + 1

    # Build turn order starting from that player, wrapping around
    turn_order = []
    current = start
    for _ in range(4):
        turn_order.append(current)
        current = 1 if current == 4 else current + 1
        
    for player_num in turn_order:
        name = f"Player {player_num}" + (" (dealer)" if player_num == dealer else "")
        hand = hands[player_num]
        print(f"{name}'s turn. Your hand is {hand}")

        if player_num == dealer:
            print(f"{name} is the dealer and must choose a trump suit.")
            while True:
                trump_suit = input(f"{name}, please choose a trump suit (H/D/C/S): ").upper()
                if trump_suit in ["H", "D", "C", "S"] and trump_suit != kittyCard[0]:
                    print(f"{name} chooses {trump_suit} as the trump suit.")
                    return player_num, trump_suit
                print("Invalid choice. Please choose a valid suit that is not the kitty card's suit.")
        else:    
            while True:
                choice = input(f"{name}, do you want to choose a trump suit or pass? (choose/pass): ").lower()
                if choice in ["choose", "pass"]:
                    break
                print("Invalid choice, please type 'choose' or 'pass'.")

            if choice == "choose":
                while True:
                    trump_suit = input(f"{name}, please choose a trump suit (H/D/C/S): ").upper()
                    if trump_suit in ["H", "D", "C", "S"] and trump_suit != kittyCard[0]:
                        print(f"{name} chooses {trump_suit} as the trump suit.")
                        return player_num, trump_suit
                    print("Invalid choice. Please choose a valid suit that is not the kitty card's suit.")

            else:
                print(f"{name} passed.")
                
    return None, None
main()