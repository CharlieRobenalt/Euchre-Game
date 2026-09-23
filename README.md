# Euchre Game & Behavior Cloning ML Model

A complete Python implementation of the trick taking game **Euchre**, designed to simulate gameplay, generate vectorized game-state datasets, and train a behavioral clone using machine learning.

## Features 
**Full Game Rules:** Standard 4-player Euchre logic, including bidding, dealer discard, trump power rankings, and bower handling.
**Turn-By-Turn ML Logging:** Encodes game-state data directly into CSV rows for imitation learning.
**Behavioral Cloning:** Trains a Random Forest Classifier on logged human decisions to predict the opimal card to play given any game-state.

## CSV Dataset Structure 
Each logged turn produces a 40-column vector:

**Column Reference**
| 0 - 23 | - 'hand_card_0' ... 'hand_card_23' - Binary vector indicating which of the 24 cards are in the player's hand.
| 24 - 26 | - 'played_1st' , 'played_2nd' , 'played_3rd' - Card IDs played so far in currrent trick (-1 if associated player has not acted yet).
