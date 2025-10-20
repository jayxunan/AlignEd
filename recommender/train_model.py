import os
import sys
import django

# Setup Django environment
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
        # Get all valid courses AND their field categories
        course_data = Course.objects.values('name', 'field_category')
        valid_courses = [c['name'] for c in course_data]
        valid_fields = list(set(c['field_category'] for c in course_data))
        
        if not valid_courses:
            print("❌ Error: No courses found in the database. Please add courses via the admin panel before training.")
            return
        print(f"✅ Found {len(valid_courses)} courses and {len(valid_fields)} fields in the database.")
    except Exception as e:
        print(f"❌ Error connecting to the database: {e}")
        return

    file_path = os.path.join(os.path.dirname(__file__), '..', 'courses_dataset.csv')
    
    try:
        df = pd.read_csv(file_path)
        original_rows = len(df)
        
        # Filter training data to include only courses/fields present in the database
        df = df[df['course'].isin(valid_courses)]
        df = df[df['field_category'].isin(valid_fields)] # Critical filter for the new column
        
        print(f"✅ Filtered training data: {len(df)} out of {original_rows} rows are for valid courses/fields.")
        if df.empty:
            print("❌ Error: No valid training data found for the courses in your database.")
            return
    except FileNotFoundError:
        print("❌ Error: 'courses_dataset.csv' not found. Please run the data generation scripts first.")
        return

    # Data Preprocessing (Fill NaNs and Encode Categorical Features)
    df['tvl_strand'].fillna('none', inplace=True)
    df['field_category'].fillna('GAS', inplace=True) 

    encoders = {}
    for column in ['shs_strand', 'tvl_strand']:
        if column in df.columns:
            le = LabelEncoder()
            # Fit and transform on all data to capture all categories
            df[column] = le.fit_transform(df[column])
            encoders[column] = le
    
    # Save the encoders for use in views.py
    encoders_path = os.path.join(os.path.dirname(__file__), 'label_encoders.joblib')
    joblib.dump(encoders, encoders_path)
    
    # Define features (inputs). Ensure the feature list is consistent across both models.
    features = [col for col in df.columns if col not in ['course', 'field_category']]
    
    # Add missing ability/interest columns if they were not in the original dataset
    for f in ['interest_building', 'interest_nature', 'interest_leading', 'interest_helping']:
        if f not in df.columns:
            df[f] = 0

    X = df[features]

    # --- MODEL 1: FIELD PREDICTION (The New Primary Model) ---
    print("\n--- Training Model 1: Field Category (Stage 1) ---")
    y_field = df['field_category']

    if len(y_field.unique()) < 2:
        print("❌ Error: The dataset contains only one type of field. Cannot train the Field model.")
        return

    X_train_field, X_test_field, y_train_field, y_test_field = train_test_split(
        X, y_field, test_size=0.2, random_state=42, stratify=y_field
    )

    field_model = RandomForestClassifier(n_estimators=100, random_state=42)
    field_model.fit(X_train_field, y_train_field)

    y_pred_field = field_model.predict(X_test_field)
    accuracy_field = accuracy_score(y_test_field, y_pred_field)

    print(f"Model 1 (Field) training complete. ACCURACY: {accuracy_field * 100:.2f}%")

    field_model_path = os.path.join(os.path.dirname(__file__), 'field_model.joblib')
    joblib.dump(field_model, field_model_path)
    print(f"✅ Field model saved to '{field_model_path}'.")


    # --- MODEL 2: COURSE PREDICTION (For Feedback Loop/Admin Tools) ---
    print("\n--- Training Model 2: Specific Course (Admin/Feedback) ---")
    y_course = df['course']
    
    if len(y_course.unique()) < 2:
        print("❌ Error: The dataset contains only one type of course. Cannot train the Course model.")
        return

    # Use a fresh split for the course model
    X_train_course, X_test_course, y_train_course, y_test_course = train_test_split(
        X, y_course, test_size=0.2, random_state=42, stratify=y_course
    )

    course_model = RandomForestClassifier(n_estimators=100, random_state=42)
    course_model.fit(X_train_course, y_train_course)

    y_pred_course = course_model.predict(X_test_course)
    accuracy_course = accuracy_score(y_test_course, y_pred_course)

    print(f"Model 2 (Course) training complete. ACCURACY: {accuracy_course * 100:.2f}%")

    course_model_path = os.path.join(os.path.dirname(__file__), 'random_forest_model.joblib')
    joblib.dump(course_model, course_model_path)
    print(f"✅ Course model saved to '{course_model_path}'.")
    print("\nModel training phase complete. System is ready for hybrid recommendations! 🎉")

if __name__ == '__main__':
    train()