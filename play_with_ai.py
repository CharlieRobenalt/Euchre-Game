import random
from unicodedata import name

class Game: 
    def __init__(self):
        self.dealer = 1
        self.score = [0, 0] # Team 1 and Team 2 scores
    def playGame(self):
        print("Let's play Euchre!")
        while max(self.score) < 10:
            hand = Hand(self.dealer)
            points = hand.playHand() # returns e.g. (0, 1) or (2, 0) etc.
            self.score[0] += points[0]
            self.score[1] += points[1]
            print(f"Score: Team 1: {self.score[0]}, Team 2: {self.score[1]}")

            self.dealer = 1 if self.dealer == 4 else self.dealer + 1  # rotate dealer

        winner = 1 if self.score[0] >= 10 else 2
        print(f"Team {winner} wins the game!")

class Hand:
    def __init__(self, dealer):
        self.dealer = dealer
        self.deck = self.resetDeck()
        self.hands = {player: self.dealHand() for player in range(1, 5)}
        self.kittyCard = self.deck.pop()
        self.trump_suit = None
        self.decisionMaker = None
        # First trick is led by the player left of the dealer
        self.leader =  1 if self.dealer == 4 else self.dealer + 1

    def playHand(self):
        self.decisionMaker, self.trump_suit = self.chooseTrumpKitty()
        if self.decisionMaker is None:
            self.decisionMaker, self.trump_suit = self.chooseTrumpNonKitty()
        else:
            self.discardCard()

        print(f"Player {self.decisionMaker} called the trump suit {self.trump_suit}.")

        tricksWon = [0, 0]
        
        for _ in range(5):   # 5 tricks per hand
            self.leader = self.playTrick()
            # after each trick, keep track of the winner so they can lead the next trick
            # adjust the hand score accordingly
            if self.leader in [1, 3]:
                tricksWon[0] += 1
            else:
                tricksWon[1] += 1

        handscore = self.adjustScore(tricksWon)
        
        return handscore  # Return the score for the hand

    def resetDeck(self):
        #Create and shuffle a euchre deck of 24 cards
        suits = ["H", "D", "C", "S"]
        ranks = [9, 10, 11, 12, 13, 14]
        #for each suit in suits and each rank in ranks, create a (suit, rank) pair
        #and add the pair to the deck
        deck = [(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck) #randomly shuffle the deck
        return deck

    def dealHand(self):
        #deal the player 5 cards
        hand = set() #hand is an empty set
        for _ in range(5):
            card = self.deck.pop() #randomly pop a card from the deck
            hand.add(card) #and add that card to the hand
        return hand

    def chooseTrumpKitty(self):
        print("Kitty Card: " + str(self.kittyCard))

        # Figure out who starts (player after the dealer, wrapping 4 -> 1)
        start = 1 if self.dealer == 4 else self.dealer + 1

        # Build turn order starting from that player, wrapping around
        turn_order = []
        current = start
        for _ in range(4):
            turn_order.append(current)
            current = 1 if current == 4 else current + 1
            
        for player_num in turn_order:
            #Print the player's turn (indicating dealer if applicable) and their hand
            name = f"Player {player_num}" + (" (dealer)" if player_num == self.dealer else "")
            hand = self.hands[player_num]
            print(f"{name}'s turn. Your hand is {hand}")

            while True:
                choice = input(f"{name}, do you want to pick it up or pass? (pick/pass): ").lower()
                if choice in ["pick", "pass"]:
                    break
                print("Invalid choice, please type 'pick' or 'pass'.")

            if choice == "pick":
                print(f"{name} says pick it up! Player {self.dealer} picks up the card, making {self.kittyCard[0]} the trump suit.")
                return player_num, self.kittyCard[0]
            else:
                print(f"{name} passed.")

        print("Everyone passed! No trump chosen this round.")
        return None, None  

    def chooseTrumpNonKitty(self):
        # Figure out who starts (player after the dealer, wrapping 4 -> 1)
        start = 1 if self.dealer == 4 else self.dealer + 1

        # Build turn order starting from that player, wrapping around
        turn_order = []
        current = start
        for _ in range(4):
            turn_order.append(current)
            current = 1 if current == 4 else current + 1

        #Ask each player if they want to choose a trump suit, and if so, which one (not the suit of the kitty card)
        for player_num in turn_order:
            name = f"Player {player_num}" + (" (dealer)" if player_num == self.dealer else "")
            hand = self.hands[player_num]
            print(f"{name}'s turn. Your hand is {hand}")

            if player_num == self.dealer:
                print(f"{name} is the dealer and must choose a trump suit.")
                while True:
                    trump_suit = input(f"{name}, please choose a trump suit (H/D/C/S): ").upper()
                    if trump_suit in ["H", "D", "C", "S"] and trump_suit != self.kittyCard[0]:
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
                        if trump_suit in ["H", "D", "C", "S"] and trump_suit != self.kittyCard[0]:
                            print(f"{name} chooses {trump_suit} as the trump suit.")
                            return player_num, trump_suit
                        print("Invalid choice. Please choose a valid suit that is not the kitty card's suit.")

                else:
                    print(f"{name} passed.")
                    
        return None, None

    def discardCard(self):

        dealer_hand = self.hands[self.dealer]
        dealer_hand.add(self.kittyCard)  # Dealer picks up the kitty card
        print(f"Dealer's hand after picking up the kitty card: {dealer_hand}")

        while True:
            discard_input = input(f"Dealer, choose a card to discard (format: SuitRank, e.g., H11 for Jack of Hearts): ")
            if len(discard_input) < 2:
                print("Invalid input. Please enter a valid card.")
                continue
            
            suit = discard_input[0].upper()
            try:
                rank = int(discard_input[1:])
            except ValueError:
                print("Invalid rank. Please enter a valid card.")
                continue
            
            discard_card = (suit, rank)
            
            if discard_card in dealer_hand:
                dealer_hand.remove(discard_card)
                print(f"Dealer discarded {discard_card}. Dealer's new hand: {dealer_hand}")
                break
            else:
                print("You cannot discard that card. Please choose a card from your hand.")

    def playTrick(self):
        rules = CardRules(self.trump_suit)
        cards_played = []
        led_suit = None

        # Build turn order starting from the leader, wrapping around
        turn_order = []
        current = self.leader
        for _ in range(4):
            turn_order.append(current)
            current = 1 if current == 4 else current + 1

        for player_num in turn_order:
            name = f"Player {player_num}"
            hand = self.hands[player_num]
            chosen_card = self.choose_card(name, hand, led_suit, rules)
            hand.remove(chosen_card)


            cards_played.append((player_num, chosen_card))

            if led_suit is None:
                led_suit = rules.effective_suit(chosen_card)
                rules.led_suit = led_suit

            print(f"{name} played {chosen_card}.")

        winner_player = self.determine_trick_winner(cards_played, rules)
        return winner_player

    def get_legal_cards(self, hand, led_suit, rules):
        if led_suit is None:
            return list(hand)  # first card of the trick — anything is legal
        else:
            legal_cards = [card for card in hand if rules.effective_suit(card) == led_suit]
            return legal_cards if legal_cards else list(hand)

    def choose_card(self, name, hand, led_suit, rules):
        legal_cards = self.get_legal_cards(hand, led_suit, rules)
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

    def determine_trick_winner(self, cards_played, rules):
        winning_card = None
        winning_player = None

        for player_num, card in cards_played:
            if winning_card is None or rules.card_value(card) > rules.card_value(winning_card):
                winning_card = card
                winning_player = player_num

        print(f"Player {winning_player} wins the trick with {winning_card}.")
        return winning_player

    def adjustScore(self, trickswon):
        handscore = [0, 0]
        # Adjusts the score based on the hand score and the player who called trump
        if self.decisionMaker in [1, 3]:  # Team 1 called trump
            if trickswon[0] == 3 or trickswon[0] == 4:  # Team 1 made their bid
                return [1,0]  # Team 1 gets 1 point
            elif trickswon[0] == 5:  # Team 1 won all 5 tricks
                return [2,0]  # Team 1 gets 3 points
            else:  # Team 1 failed to make their bid
                return [0, 2]  # Team 2 gets 2 points
        else:  # Team 2 called trump
            if trickswon[1] == 3 or trickswon[1] == 4:  # Team 2 made their bid
                return [0, 1]  # Team 2 gets 1 point
            elif trickswon[1] == 5:  # Team 2 won all 5 tricks
                return [0, 2]  # Team 2 gets 3 points
            else:  # Team 2 failed to make their bid
                return [2, 0]  # Team 1 gets 2 points


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
                return 100  # Right Bower always wins
            elif rank == 11 and suit == self.left_bower_suit:
                return 99  # Left Bower only loses to right bower
            else:
                return rank + 50  # Regular trump cards: rank (9-14) + 50, always outranks non-trump cards
        elif suit == self.led_suit:
            return rank  # Non-trump cards of the led suit are ranked normally
        else:   
            return -1  # Non-trump cards of a non-led suit are ranked lowest and can't win the trick


game1 = Game()
game1.playGame()