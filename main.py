def main():
    print("Let's play Euchre!")
    deck = resetDeck()
    player1_hand = dealHand(deck)
    player2_hand = dealHand(deck)
    player3_hand = dealHand(deck)
    user_hand = dealHand(deck)
    print("Player 1's hand:", player1_hand)
    print("Player 2's hand:", player2_hand)
    print("Player 3's hand:", player3_hand)
    print("Your hand:", user_hand)

def resetDeck():
    suits = ["H", "D", "C", "S"]
    ranks = [9, 10, 11, 12, 13, 14]
    deck = {(suit, rank) for suit in suits for rank in ranks}
    return deck

def dealHand(deck):
    #deal the player 5 cards reserve the final 4 cards for the kitty
    pass

main()