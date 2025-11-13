import os
import sys
import django
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib
import warnings

# --- START of Fix: Import SettingWithCopyWarning from the correct place ---
try:
    from pandas.errors import SettingWithCopyWarning
except ImportError:
    # Fallback for older Pandas versions
    SettingWithCopyWarning = None 
    
# Suppress SettingWithCopyWarning, which can occur during DataFrame operations
if SettingWithCopyWarning:
    warnings.filterwarnings('ignore', category=SettingWithCopyWarning)
# --- END of Fix ---


# Setup Django environment
# WARNING: Adjust 'aligned' to your actual project name if different
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aligned.settings')
django.setup()
from recommender.models import Course


def train():

    try:
        # Get all valid courses AND their field categories from the database
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

    # Define paths
    file_path = os.path.join(os.path.dirname(__file__), '..', 'courses_dataset.csv')
    encoders_path = os.path.join(os.path.dirname(__file__), 'label_encoders.joblib')
    field_model_path = os.path.join(os.path.dirname(__file__), 'field_model.joblib')
    course_model_path = os.path.join(os.path.dirname(__file__), 'random_forest_model.joblib')
    
    try:
        df = pd.read_csv(file_path)
        original_rows = len(df)
        
        # Filter training data to include only courses/fields present in the database
        df = df[df['course'].isin(valid_courses)]
        df = df[df['field_category'].isin(valid_fields)]
        
        print(f"✅ Filtered training data: {len(df)} out of {original_rows} rows are for valid courses/fields.")
        if df.empty:
            print("❌ Error: No valid training data found for the courses in your database.")
            return
    except FileNotFoundError:
        print("❌ Error: 'courses_dataset.csv' not found. Please run the data generation scripts first.")
        return

    # --- Data Preprocessing ---
    df['tvl_strand'].fillna('none', inplace=True)
    df['shs_strand'].fillna('GAS', inplace=True) # Fallback for missing SHS
    df['field_category'].fillna('GAS', inplace=True) 

    encoders = {}
    
    # 1. Encode Categorical Features
    CATEGORICAL_COLUMNS = ['shs_strand', 'tvl_strand']
    for column in CATEGORICAL_COLUMNS:
        if column in df.columns:
            le = LabelEncoder()
            # Fit and transform, ensuring data is treated as strings
            df[column] = le.fit_transform(df[column].astype(str))
            encoders[column] = le
    
    # Save the encoders for use in views.py
    joblib.dump(encoders, encoders_path)
    
    # 2. Define Feature Set Dynamically
    # We exclude the target variables and the original categorical string columns
    TARGET_COLUMNS = ['course', 'field_category']
    
    # Features include encoded categories and all 50 trait/aptitude scores
    # This automatically picks up all your trait columns (interest_, ability_, dmgt_)
    features = [col for col in df.columns if col not in TARGET_COLUMNS]
    
    # Convert all feature columns to numeric and handle potential NaNs
    df[features] = df[features].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    X = df[features]
    print(f"✅ Feature set established. Training with {len(features)} total features.")


    # --- MODEL 1: FIELD PREDICTION (Stage 1) ---
    print("\n--- Training Model 1: Field Category (Stage 1) ---")
    y_field = df['field_category']

    if len(y_field.unique()) < 2:
        print("❌ Error: The dataset contains only one type of field. Cannot train the Field model.")
        return

    X_train_field, X_test_field, y_train_field, y_test_field = train_test_split(
        X, y_field, test_size=0.2, random_state=42, stratify=y_field
    )

    field_model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    field_model.fit(X_train_field, y_train_field)

    y_pred_field = field_model.predict(X_test_field)
    accuracy_field = accuracy_score(y_test_field, y_pred_field)

    print(f"Model 1 (Field) training complete. ACCURACY: {accuracy_field * 100:.2f}%")

    joblib.dump(field_model, field_model_path)
    print(f"✅ Field model saved to '{field_model_path}'.")


    # --- MODEL 2: COURSE PREDICTION (Admin/Feedback) ---
    print("\n--- Training Model 2: Specific Course (Admin/Feedback) ---")
    y_course = df['course']
    
    if len(y_course.unique()) < 2:
        print("❌ Error: The dataset contains only one type of course. Cannot train the Course model.")
        return

    # Use a fresh split for the course model
    X_train_course, X_test_course, y_train_course, y_test_course = train_test_split(
        X, y_course, test_size=0.2, random_state=42, stratify=y_course
    )

    course_model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    course_model.fit(X_train_course, y_train_course)

    y_pred_course = course_model.predict(X_test_course)
    accuracy_course = accuracy_score(y_test_course, y_pred_course)

    print(f"Model 2 (Course) training complete. ACCURACY: {accuracy_course * 100:.2f}%")

    joblib.dump(course_model, course_model_path)
    print(f"✅ Course model saved to '{course_model_path}'.")
    print("\nModel training phase complete. System is ready for hybrid recommendations! 🎉")

if __name__ == '__main__':
    train()