# simulate_data.py

import pandas as pd
import numpy as np
import random
import os

# --- CRITICAL: Copy the FIELD_CATEGORIES and COURSE_TO_FIELD map from generate_large_dataset.py ---
# This ensures that when a course is chosen, its field category can be determined.
FIELD_CATEGORIES = {
    'TECH': ['Computer Science', 'Information Technology', 'Information Systems', 'Information Security', 'Game Development', 'Web & Mobile Development', 'Applied Statistics', 'Data Science', 'AI Engineering', 'Technical Communication'],
    'ENG': ['Architecture', 'Interior Design', 'Industrial Design', 'Chemical Engineering', 'Civil Engineering', 'Computer Engineering', 'Electrical Engineering', 'Electronics Engineering', 'Industrial Engineering', 'Mechanical Engineering', 'Environmental & Sanitary Engineering', 'Biological Engineering', 'Energy Engineering', 'Manufacturing Engineering', 'Materials Science & Engineering', 'Geodetic Engineering', 'Metallurgical Engineering', 'Mining Engineering', 'Management Engineering', 'Mechatronics Technology', 'Railway Engineering'],
    'BUS': ['Accountancy', 'Business Administration', 'Entrepreneurship', 'Management Accounting', 'Financial Management', 'Marketing Management', 'Human Resource Management', 'Office Administration', 'Business Economics', 'Economics', 'Legal Management', 'Cooperatives'],
    'HEALTH': ['Biology', 'Marine Biology', 'Molecular Biology & Biotechnology', 'Physics', 'Chemistry', 'Nursing', 'Medical Technology', 'Pharmacy', 'Physical Therapy', 'Nutrition and Dietetics', 'Community Nutrition', 'Food Technology', 'Family Life and Child Development'],
    'SOCIAL': ['Psychology', 'Sociology', 'Anthropology', 'History', 'Philosophy', 'Political Science', 'Political Economy', 'Development Studies', 'Social Work', 'International Studies', 'Southeast Asian Studies', 'European Languages', 'Philippine Studies', 'Linguistics', 'Behavioral Sciences'],
    'MEDIA': ['Communication / Communication Arts', 'Broadcast Communication', 'Communication Research', 'Journalism', 'Film', 'Theatre Arts', 'Art Studies / Fine Arts', 'Art History', 'Painting', 'Sculpture', 'Creative Writing', 'Malikhaing Pagsulat (Creative Writing in Filipino)', 'English Studies / Literature', 'Filipino', 'Music', 'Speech Communication', 'Visual Communication'],
    'EDUC': ['Elementary Education (BEEd)', 'Secondary Education (BSEd)', 'Early Childhood Education', 'Library & Information Science', 'Physical Education', 'Sports & Wellness Management', 'Art Education'],
    'PUB': ['Public Administration', 'Community Development'],
    'HOSP': ['Hospitality Management', 'Tourism Management', 'Transportation Management', 'Hotel, Restaurant & Institutional Management'],
    'APPLIED': ['Criminology', 'Agriculture', 'Landscape Architecture', 'Clothing Technology', 'Electrical Installation', 'Automotive Technology', 'Voice'],
}

COURSE_TO_FIELD = {course: field for field, courses in FIELD_CATEGORIES.items() for course in courses}

# Redefine PROFILES to include the courses from the massive list, or at least a representative sample
# For simplicity and to use the existing data structure, we'll keep the SHS-based profiles,
# but ensure the courses listed here are from the new expanded list.
PROFILES = {
    "STEM_Tech": {
        "interests": {"science": (5, 5), "tech": (5, 5), "building": (4, 5), "arts": (1, 2), "helping": (1, 2)},
        "abilities": {"logic": (5, 5), "practical": (3, 4), "comm": (2, 3)},
        "courses": ['Computer Science', 'Information Technology', 'Data Science', 'Web & Mobile Development', 'Computer Engineering', 'Chemical Engineering', 'Physics', 'Biology'] # Updated sample courses
    },
    "STEM_Engineering": {
        "interests": {"science": (5, 5), "building": (5, 5), "tech": (4, 5), "arts": (1, 2)},
        "abilities": {"logic": (5, 5), "practical": (5, 5), "teamwork": (3, 4)},
        "courses": ['Civil Engineering', 'Mechanical Engineering', 'Electronics Engineering', 'Architecture', 'Materials Science & Engineering'] # Updated sample courses
    },
    "HUMSS_Social": {
        "interests": {"teaching": (5, 5), "helping": (4, 5), "leading": (4, 5), "arts": (3, 5), "science": (1, 2)},
        "abilities": {"comm": (5, 5), "creativity": (4, 5), "teamwork": (4, 5)},
        "courses": ['Psychology', 'Elementary Education (BEEd)', 'Communication / Communication Arts', 'Political Science', 'Public Administration', 'Social Work'] # Updated sample courses
    },
    "ABM_Business": {
        "interests": {"business": (5, 5), "leading": (5, 5), "tech": (2, 4), "arts": (1, 2)},
        "abilities": {"comm": (4, 5), "teamwork": (5, 5), "logic": (3, 4)},
        "courses": ['Business Administration', 'Accountancy', 'Entrepreneurship', 'Marketing Management', 'Financial Management', 'Economics'] # Updated sample courses
    },
    "TVL_Practical": {
        "interests": {"building": (5, 5), "tech": (4, 5), "sports": (3, 4), "arts": (1, 2)},
        "abilities": {"practical": (5, 5), "teamwork": (4, 5), "logic": (3, 4)},
        "courses": ['Automotive Technology', 'Electrical Installation', 'Criminology', 'Agriculture', 'Clothing Technology'] # Updated sample courses
    },
      "Health_Sciences": {
        "interests": {"science": (5, 5), "helping": (5, 5), "teaching": (3, 4), "tech": (1, 2)},
        "abilities": {"logic": (4, 5), "comm": (4, 5), "practical": (4, 5)},
        "courses": ['Nursing', 'Medical Technology', 'Pharmacy', 'Physical Therapy', 'Nutrition and Dietetics'] # Updated sample courses
    },
    # Note: Other fields (MEDIA, HOSP, etc.) are implicitly covered in GAS or the above profiles
}


def generate_simulated_data(num_rows=150):
    data = []
    for _ in range(num_rows):
        profile_name = random.choice(list(PROFILES.keys()))
        profile = PROFILES[profile_name]
        
        if "STEM" in profile_name: strand = "STEM"
        elif "HUMSS" in profile_name: strand = "HUMSS"
        elif "ABM" in profile_name: strand = "ABM"
        elif "TVL" in profile_name: strand = "TVL"
        else: strand = "GAS"

        course = random.choice(profile['courses'])
        
        # --- CRITICAL CHANGE: Look up the Field Category for the chosen course ---
        field_category = COURSE_TO_FIELD.get(course, 'GAS') # Default to 'GAS' if not found
        
        # --- ADD 'field_category' TO THE ROW ---
        row = {
            'shs_strand': strand, 
            'tvl_strand': 'ICT' if strand == "TVL" else 'none', 
            'course': course, 
            'field_category': field_category # This is the key addition
        }
        
        # Define all possible interests and abilities
        interests = ['science', 'arts', 'teaching', 'business', 'tech', 'design', 'sports', 'building', 'nature', 'leading', 'helping']
        abilities = ['logic', 'creativity', 'comm', 'practical', 'teamwork']

        for i in interests:
            low, high = profile['interests'].get(i, (1, 3)) 
            row[f'interest_{i}'] = random.randint(low, high)
        for a in abilities:
            low, high = profile['abilities'].get(a, (1, 3))
            row[f'ability_{a}'] = random.randint(low, high)
        data.append(row)
    
    return pd.DataFrame(data)

if __name__ == '__main__':
    print("Generating 150 simulated student responses with the new field category...")
    simulated_df = generate_simulated_data(150)
    
    cleaned_real_data_path = 'courses_dataset.csv'
    
    if os.path.exists(cleaned_real_data_path):
        try:
            real_df = pd.read_csv(cleaned_real_data_path)
            print(f"Found {len(real_df)} existing training responses. Combining with simulated data.")
            
            # Ensure the real_df has the new 'field_category' column (should be there if you ran generate_large_dataset.py)
            if 'field_category' not in real_df.columns:
                 print("WARNING: 'field_category' column missing in existing data. Re-running generate_large_dataset.py is recommended.")

            # Ensure all columns match before concatenating
            for col in simulated_df.columns:
                if col not in real_df.columns:
                    real_df[col] = 0
            
            combined_df = pd.concat([real_df, simulated_df], ignore_index=True)
            
        except pd.errors.EmptyDataError:
            print("Existing survey data file is empty. Using only simulated data.")
            combined_df = simulated_df
    else:
        print("No existing courses_dataset.csv found. Using only simulated data. Note: Run generate_large_dataset.py first!")
        combined_df = simulated_df

    combined_df = combined_df[simulated_df.columns] # Ensure consistent column order
    
    # Save the combined dataset (overwriting the large dataset with the extra simulated data)
    combined_df.to_csv(cleaned_real_data_path, index=False)
    
    print(f"\nSuccessfully updated '{cleaned_real_data_path}' with {len(combined_df)} total rows.")
    print("\n----------------------------------------------------")
    print("CRITICAL: Next step is to update and run train_model.py to create the two new models (field_model.joblib and random_forest_model.joblib).")