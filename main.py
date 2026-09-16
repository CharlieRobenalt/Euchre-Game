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

    deck = resetDeck() #Create and shuffle the deck
    player1_hand = dealHand(deck) #deal each player their 5 cards
    player2_hand = dealHand(deck)
    player3_hand = dealHand(deck)
    player4_hand = dealHand(deck)

    kittyCard = deck.pop()  # The top card of the remaining deck is the kitty card
    print("Kitty Card: " + str(kittyCard))

    decisionMaker, trump_suit = chooseTrumpKitty(kittyCard, dealer, player1_hand, player2_hand, player3_hand, player4_hand)

    if decisionMaker is None:
        decisionMaker, trump_suit = chooseTrumpNontKitty(kittyCard, dealer, player1_hand, player2_hand, player3_hand, player4_hand)

    print(f"Player {decisionMaker} called the trump suit {trump_suit}.")

    hand_score = playHand(player1_hand, player2_hand, player3_hand, player4_hand, trump_suit, dealer)
    if hand_score[0] > hand_score[1]:
        score[0] += 1
        print("Team 1 wins the hand!")
    else:
        score[1] += 1
        print("Team 2 wins the hand!")

def resetDeck():
    #Create and shuffle a euchre deck of 24 cards
    suits = ["H", "D", "C", "S"]
    ranks = [9, 10, 11, 12, 13, 14]
    #for each suit in suits and each rank in ranks, create a (suit, rank) pair
    #and add the pair to the deck
    deck = [(suit, rank) for suit in suits for rank in ranks]
    random.shuffle(deck) #randomly shuffle the deck
    return deck

def dealHand(deck):
    #deal the player 5 cards
    hand = set() #hand is an empty set
    for _ in range(5):
        card = deck.pop() #randomly pop a card from the deck
        hand.add(card) #and add that card to the hand
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
            print(f"{name} passed.")re

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

def playHand(player1_hand, player2_hand, player3_hand, player4_hand, trump_suit, dealer):
    hands = {1: player1_hand, 2: player2_hand, 3: player3_hand, 4: player4_hand}
    handScore = [0, 0]

    # First trick is led by the player left of the dealer
    leader = 1 if dealer == 4 else dealer + 1

    for _ in range(5):   # 5 tricks per hand
        leader = playTrick(hands, trump_suit, leader)
        # after each trick, the winner leads the next one
        if leader in [1, 3]:
            handScore[0] += 1
        else:
            handScore[1] += 1

    return handScore  # Return the score for the hand
    

def playTrick(hands, trump_suit, leader):
    # Implement the logic for playing trick
    rules = CardRules(trump_suit)
    cards_played = []
    led_suit = None

     # Build turn order starting from that player, wrapping around
    turn_order = []
    current = leader
    for _ in range(4):
        turn_order.append(current)
        current = 1 if current == 4 else current + 1

    for player_num in turn_order:
        name = f"Player {player_num}"
        hand = hands[player_num]
        chosen_card = choose_card(name, hand, led_suit, rules)
        hands[player_num].remove(chosen_card)
        cards_played.append((player_num, chosen_card))

        if led_suit is None:
            led_suit = rules.effective_suit(chosen_card)  # Set the led suit based on the first card played
            rules.led_suit = led_suit  # Update the rules with the led suit

        print(f"{name} played {chosen_card}.")

    winner_player = determine_trick_winner(cards_played, rules)
    return winner_player  # Return the player number of the trick winner

def get_legal_cards(hand, led_suit, rules):
    #Returns the cards in hand that are legal to play, given the led suit.
    if led_suit is None:
        return list(hand)  # first card of the trick — anything is legal
    else:
        legal_cards = [card for card in hand if rules.effective_suit(card) == led_suit]
        return legal_cards if legal_cards else list(hand)  # If no cards of the led suit, can play any card

def choose_card(name, hand, led_suit, rules):
    legal_cards = get_legal_cards(hand, led_suit, rules)
    print(f"{name}, your hand is {hand}. Legal cards to play: {legal_cards}")
    
    while True:
        card_input = input(f"{name}, choose a card to play (format: SuitRank, e.g., H11 for Jack of Hearts): ")
        if len(card_input) < 2:
            print("Invalid input. Please enter a valid card.")
            continue
        
        suit = card_input[0].upper()
        try:
            rank = int(card_input[1:])
        except ValueError:
            print("Invalid rank. Please enter a valid card.")
            continue
        
        chosen_card = (suit, rank)
        
        if chosen_card in legal_cards:
            return chosen_card
        else:
            print("You cannot play that card. Please choose a legal card.")

def determine_trick_winner(cards_played, rules):
    winning_card = None
    winning_player = None

    for player_num, card in cards_played:
        if winning_card is None or rules.card_value(card) > rules.card_value(winning_card):
            winning_card = card
            winning_player = player_num

    print(f"Player {winning_player} wins the trick with {winning_card}.")
    return winning_player

main()