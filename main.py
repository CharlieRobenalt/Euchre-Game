import random

def main():
    print("Let's play Euchre!")
    deck = resetDeck()
    player1_hand = dealHand(deck)
    player2_hand = dealHand(deck)
    player3_hand = dealHand(deck)
    user_hand = dealHand(deck)

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