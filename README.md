# Euchre Game & Behavior Cloning ML Model

A complete Python implementation of the trick taking game **Euchre**, designed to simulate gameplay, generate vectorized game-state datasets, and train a behavioral clone using machine learning.

## Features 
- **Full Game Rules:** Standard 4-player Euchre logic, including bidding, dealer discard, trump power rankings, and bower handling.
- **Turn-By-Turn ML Logging:** Encodes game-state data directly into CSV rows for imitation learning.
- **Behavioral Cloning:** Trains a Random Forest Classifier on logged human decisions to predict the opimal card to play given any game-state.

## CSV Dataset Structure 
Each logged turn produces a 40-column vector:

**Column Reference**

| Columns | Feature Name | Description |
| :--- | :--- | :--- |
| **0–23** | `hand_card_0` ... `hand_card_23` | Binary vector indicating which of the 24 cards are in the player's hand. |
| **24–26** | `played_1st`, `played_2nd`, `played_3rd` | Card IDs played so far in the current trick (`-1` if seat has not acted yet). |
| **27** | `partner_played` | `1` if the player's partner has acted this trick; `0` otherwise. |
| **28** | `partner_card` | Card ID played by the partner (`-1` if not yet played). |
| **29** | `partner_winning` | `1` if the partner currently holds the highest card; `0` otherwise. |
| **30** | `trump` | The trump suit integer (`0`=Hearts, `1`=Diamonds, `2`=Clubs, `3`=Spades). |
| **31** | `lead_card` | The card ID that led the current trick (`-1` if leading). |
| **32–38** | `trump_played_*` | 7-element binary vector tracking played trumps (Right Bower, Left Bower, A, K, Q, 10, 9). |
| **39** | `chosen_card` | **Target label**: Card ID selected by the player. |
