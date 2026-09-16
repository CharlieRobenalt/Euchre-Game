import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier

def train_clone():
    # 1. Load your collected gameplay
    df = pd.read_csv("my_moves.csv")
    
    # 2. Separate features (game state) and label (your choice)
    X = df.drop(columns=["chosen_card"])
    y = df["chosen_card"]

    # 3. Train the classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # 4. Save the model locally
    with open("my_ai_model.pkl", "wb") as f:
        pickle.dump(model, f)
        
    print("Model trained and saved as 'my_ai_model.pkl'!")

if __name__ == "__main__":
    train_clone()