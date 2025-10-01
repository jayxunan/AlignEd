import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib
import os

def train():
    file_path = os.path.join(os.path.dirname(__file__), '..', 'courses_dataset.csv')
    
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            print("❌ Error: 'courses_dataset.csv' is empty. Cannot train model.")
            return
    except FileNotFoundError:
        print("❌ Error: 'courses_dataset.csv' not found. Please run the cleaning and simulation scripts first.")
        return

    df['tvl_strand'].fillna('none', inplace=True)

    encoders = {}
    for column in ['shs_strand', 'tvl_strand']:
        le = LabelEncoder()
        df[column] = le.fit_transform(df[column])
        encoders[column] = le

    features = [col for col in df.columns if col != 'course']
    X = df[features]
    y = df['course']

    # Stratify ensures the test set has the same course proportions as the full dataset.
    # This gives a more reliable accuracy score.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("✅ Model training complete.")
    print("-----------------------------------------")
    print(f"📊 MODEL ACCURACY: {accuracy * 100:.2f}%")
    print("-----------------------------------------")
    print("(This score represents how well the model predicted courses on the unseen test data.)")

    model_path = os.path.join(os.path.dirname(__file__), 'random_forest_model.joblib')
    encoders_path = os.path.join(os.path.dirname(__file__), 'label_encoders.joblib')
    
    joblib.dump(model, model_path)
    joblib.dump(encoders, encoders_path)
    print("\n✅ Model and encoders saved successfully.")

if __name__ == '__main__':
    train()

