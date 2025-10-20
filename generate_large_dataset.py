# generate_large_dataset.py

import pandas as pd
import numpy as np
import random

# --- 1. COURSE DEFINITIONS & FIELD MAPPING ---

# Define the ten major field categories and list all the new courses within them.
FIELD_CATEGORIES = {
    'TECH': ['Computer Science', 'Information Technology', 'Information Systems', 'Information Security', 'Game Development', 'Web & Mobile Development', 'Applied Statistics', 'Data Science', 'AI Engineering', 'Technical Communication'],
    'ENG': ['Architecture', 'Interior Design', 'Industrial Design', 'Chemical Engineering', 'Civil Engineering', 'Computer Engineering', 'Electrical Engineering', 'Electronics Engineering', 'Industrial Engineering', 'Mechanical Engineering', 'Environmental & Sanitary Engineering', 'Biological Engineering', 'Energy Engineering', 'Manufacturing Engineering', 'Materials Science & Engineering', 'Geodetic Engineering', 'Metallurgical Engineering', 'Mining Engineering', 'Management Engineering', 'Mechatronics Technology', 'Railway Engineering'],
    'BUS': ['Accountancy', 'Business Administration', 'Entrepreneurship', 'Management Accounting', 'Financial Management', 'Marketing Management', 'Human Resource Management', 'Office Administration', 'Business Economics', 'Economics', 'Legal Management', 'Cooperatives'],
    'HEALTH': ['Biology', 'Marine Biology', 'Molecular Biology & Biotechnology', 'Physics', 'Chemistry', 'Nursing', 'Medical Technology', 'Pharmacy', 'Physical Therapy', 'Nutrition and Dietetics', 'Community Nutrition', 'Food Technology', 'Family Life and Child Development'],
    'SOCIAL': ['Psychology', 'Sociology', 'Anthropology', 'History', 'Philosophy', 'Political Science', 'Political Economy', 'Development Studies', 'Social Work', 'International Studies', 'Southeast Asian Studies', 'European Languages', 'Philippine Studies', 'Linguistics', 'Behavioral Sciences'],
    'MEDIA': ['Communication / Communication Arts', 'Broadcast Communication', 'Communication Research', 'Journalism', 'Film', 'Theatre Arts', 'Art Studies / Fine Arts', 'Art History', 'Painting', 'Sculpture', 'Creative Writing', 'Malikhaang Pagsulat (Creative Writing in Filipino)', 'English Studies / Literature', 'Filipino', 'Music', 'Speech Communication', 'Visual Communication'],
    'EDUC': ['Elementary Education (BEEd)', 'Secondary Education (BSEd)', 'Early Childhood Education', 'Library & Information Science', 'Physical Education', 'Sports & Wellness Management', 'Art Education'],
    'PUB': ['Public Administration', 'Community Development'],
    'HOSP': ['Hospitality Management', 'Tourism Management', 'Transportation Management', 'Hotel, Restaurant & Institutional Management'],
    'APPLIED': ['Criminology', 'Agriculture', 'Landscape Architecture', 'Clothing Technology', 'Electrical Installation', 'Automotive Technology', 'Voice'],
}

# Generate a reverse map for easy lookup: Course Name -> Field Category
COURSE_TO_FIELD = {course: field for field, courses in FIELD_CATEGORIES.items() for course in courses}
COURSES = list(COURSE_TO_FIELD.keys()) # All 100+ courses

# --- 2. BASELINE FIELD PROFILES (for Data Generation) ---
# Define a general interest/ability profile for each broad field.

PROFILES_BY_FIELD = {
    # Tech/Data requires Logic and Tech interest
    'TECH': {'interests': {'tech': (5,5), 'science': (4,5), 'building': (3,4)}, 'abilities': {'logic': (5,5), 'practical': (4,5), 'creativity': (3,4)}, 'shs_strand': 'STEM'},
    # Engineering/Arch requires Building interest, Logic, and Practical ability
    'ENG': {'interests': {'building': (5,5), 'science': (4,5), 'tech': (3,4)}, 'abilities': {'logic': (5,5), 'practical': (5,5), 'creativity': (4,5)}, 'shs_strand': 'STEM'},
    # Business requires Business interest, Comm, and Teamwork
    'BUS': {'interests': {'business': (5,5), 'leading': (4,5), 'science': (2,3)}, 'abilities': {'comm': (5,5), 'teamwork': (4,5), 'logic': (4,5)}, 'shs_strand': 'ABM'},
    # Health/Science requires Science interest, Helping, and Logic/Practical ability
    'HEALTH': {'interests': {'helping': (5,5), 'science': (5,5), 'nature': (3,4)}, 'abilities': {'logic': (4,5), 'practical': (4,5), 'comm': (4,5)}, 'shs_strand': 'STEM'},
    # Social Sciences/Hum requires Helping, Teaching, and Comm/Creativity
    'SOCIAL': {'interests': {'helping': (5,5), 'teaching': (4,5), 'arts': (3,5)}, 'abilities': {'comm': (5,5), 'creativity': (4,5), 'logic': (3,4)}, 'shs_strand': 'HUMSS'},
    # Media/Arts requires Arts, Design, and Creativity/Comm
    'MEDIA': {'interests': {'arts': (5,5), 'design': (5,5), 'tech': (3,4)}, 'abilities': {'creativity': (5,5), 'comm': (4,5), 'practical': (2,3)}, 'shs_strand': 'GAS'},
    # Education requires Teaching, Helping, Comm, and Teamwork
    'EDUC': {'interests': {'teaching': (5,5), 'helping': (4,5), 'science': (1,2)}, 'abilities': {'comm': (5,5), 'teamwork': (4,5), 'creativity': (3,4)}, 'shs_strand': 'HUMSS'},
    # Public Service requires Leading, Helping, and Comm
    'PUB': {'interests': {'leading': (5,5), 'helping': (4,5), 'business': (3,4)}, 'abilities': {'comm': (5,5), 'logic': (4,5), 'teamwork': (4,5)}, 'shs_strand': 'HUMSS'},
    # Hospitality requires Helping, Teamwork, and Comm
    'HOSP': {'interests': {'helping': (5,5), 'leading': (4,5), 'business': (3,4)}, 'abilities': {'teamwork': (5,5), 'comm': (5,5), 'practical': (3,4)}, 'shs_strand': 'HESS'}, # Using HESS for specific SHS Strand
    # Applied/Vocational requires Building, Tech, and Practical ability
    'APPLIED': {'interests': {'building': (5,5), 'tech': (4,5), 'sports': (3,4)}, 'abilities': {'practical': (5,5), 'logic': (3,4), 'teamwork': (4,5)}, 'shs_strand': 'TVL'},
}


# --- 3. GENERATION LOGIC ---

def generate_row_for_course(course):
    field_category = COURSE_TO_FIELD.get(course)
    if not field_category:
        return None
        
    profile = PROFILES_BY_FIELD[field_category]

    # Map SHS strand from the profile
    strand = profile.get('shs_strand', 'GAS')

    # --- CRITICAL CHANGE: ADD THE NEW 'field_category' COLUMN ---
    row = {'shs_strand': strand, 'tvl_strand': 'ICT' if strand == "TVL" else 'none', 'course': course, 'field_category': field_category}

    # Define all possible interests and abilities for data consistency
    all_interests = ['science', 'arts', 'teaching', 'business', 'tech', 'design', 'sports', 'building', 'nature', 'leading', 'helping']
    all_abilities = ['logic', 'creativity', 'comm', 'practical', 'teamwork']

    # Generate ratings based on the field's baseline profile
    for i in all_interests:
        # Default to a middle-low range (1, 3) if not explicitly set in the field profile
        low, high = profile['interests'].get(i, (1, 3))
        row[f'interest_{i}'] = random.randint(low, high)
    for a in all_abilities:
        low, high = profile['abilities'].get(a, (1, 3))
        row[f'ability_{a}'] = random.randint(low, high)
        
    return row

if __name__ == "__main__":
    # --- Bias Mitigation Implemented Here: Equal rows per course ---
    NUM_ROWS_PER_COURSE = 20 # Lowered from 60 to manage file size, but still ensures balance
    total_rows = len(COURSES) * NUM_ROWS_PER_COURSE
    
    print(f"Starting data generation for the expanded list of {len(COURSES)} courses.")
    print(f"Target: {NUM_ROWS_PER_COURSE} rows for each course. Total rows: {total_rows}.")
    
    all_data = []
    for course in COURSES:
        for _ in range(NUM_ROWS_PER_COURSE):
            all_data.append(generate_row_for_course(course))

    df = pd.DataFrame([data for data in all_data if data is not None])

    # Shuffle the dataset to mix everything up
    df = df.sample(frac=1).reset_index(drop=True)
    
    output_path = 'courses_dataset.csv'
    df.to_csv(output_path, index=False)
    
    print("\n----------------------------------------------------")
    print(f"Successfully generated a balanced and massive dataset!")
    print(f"Saved {len(df)} rows to '{output_path}'.")
    print("----------------------------------------------------\n")
    print("NEXT STEP: You must run the data cleaning/combining script, and then re-train your models.")