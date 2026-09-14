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

main()