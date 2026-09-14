def main():
    print("Let's play Euchre!")
    deck = resetDeck()
    print(deck)

def resetDeck():
    suits = ["H", "D", "C", "S"]
    ranks = [9, 10, 11, 12, 13, 14]
    deck = [(suit, rank) for suit in suits for rank in ranks]
    return deck

def dealCards(deck):
    #deal each player 5 cards reserve the final 4 cards for the kitty
    pass

main()