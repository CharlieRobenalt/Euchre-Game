import random

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
    chooseTrump(kittyCard, dealer, player1_hand, player2_hand, player3_hand, player4_hand)

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

def chooseTrump(kittyCard, dealer, player1_hand, player2_hand, player3_hand, player4_hand):
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
            return dealer, kittyCard[0]
        else:
            print(f"{name} passed.")

    print("Everyone passed! No trump chosen this round.")
    return None, None  
main()