import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def train_clone():
    # 1. Load the collected gameplay
    df = pd.read_csv("my_moves.csv")
    
    # 2. Separate features (game state) and label (the choice)
    X = df.drop(columns=["chosen_card"])
    y = df["chosen_card"]

    # 3. Split into train/test so you can check if the model is actually learning
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train the classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. Check accuracy on data it hasn't seen
    preds = model.predict(X_test)
    print(f"Test accuracy: {accuracy_score(y_test, preds):.2%}")

    # 6. Save the model locally
    with open("my_ai_model.pkl", "wb") as f:
        pickle.dump(model, f)
        
    print("Model trained and saved as 'my_ai_model.pkl'!")

if __name__ == "__main__":
    train_clone()