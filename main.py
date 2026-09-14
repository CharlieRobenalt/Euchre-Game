def main():
    print("Let's play Euchre!")
    desk = resetDeck()

def resetDeck():
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = [9, 10, 11, 12, 13, 14]
    deck = [(suit, rank) for suit in suits for rank in ranks]
    return deck

def dealCards(deck):
    #deal each player 5 cards reserve the final 4 cards for the kitty
    pass