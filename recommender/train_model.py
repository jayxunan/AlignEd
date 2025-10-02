import os
import sys
import django

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aligned.settings')
django.setup()
from recommender.models import Course


def train():

    try:
        valid_courses = list(Course.objects.values_list('name', flat=True))
        if not valid_courses:
            print("❌ Error: No courses found in the database. Please add courses via the admin panel before training.")
            return
        print(f"✅ Found {len(valid_courses)} courses in the database to train on.")
    except Exception as e:
        print(f"❌ Error connecting to the database: {e}")
        return

    file_path = os.path.join(os.path.dirname(__file__), '..', 'courses_dataset.csv')
    
    try:
        df = pd.read_csv(file_path)
        original_rows = len(df)
        df = df[df['course'].isin(valid_courses)]
        print(f"✅ Filtered training data: {len(df)} out of {original_rows} rows are for valid courses.")
        if df.empty:
            print("❌ Error: No valid training data found for the courses in your database.")
            return
    except FileNotFoundError:
        print("❌ Error: 'courses_dataset.csv' not found. Please run the data generation scripts first.")
        return

    df['tvl_strand'].fillna('none', inplace=True)
    encoders = {}
    for column in ['shs_strand', 'tvl_strand']:
        if column in df.columns:
            le = LabelEncoder()
            df[column] = le.fit_transform(df[column])
            encoders[column] = le

    features = [col for col in df.columns if col != 'course']
    for f in ['interest_building', 'interest_nature', 'interest_leading', 'interest_helping']:
        if f not in df.columns:
            df[f] = 0
    
    X = df[features]
    y = df['course']

    if len(y.unique()) < 2:
        print("❌ Error: The filtered dataset contains only one type of course. Cannot train the model.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("Model training complete.")
    print(f"MODEL ACCURACY: {accuracy * 100:.2f}%")

    model_path = os.path.join(os.path.dirname(__file__), 'random_forest_model.joblib')
    encoders_path = os.path.join(os.path.dirname(__file__), 'label_encoders.joblib')
    
    joblib.dump(model, model_path)
    joblib.dump(encoders, encoders_path)
    print("\nModel and encoders saved successfully.")

if __name__ == '__main__':
    train()

