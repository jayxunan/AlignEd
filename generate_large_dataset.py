# generate_large_dataset.py

import pandas as pd
import numpy as np
import random

# --- 1. MASTER LIST OF ALL 50 ASSESSMENT FIELDS (From models.py update) ---
# Separated into Interests (25) and Aptitudes/Volitional Traits (25)
ALL_INTERESTS = [
    'interest_research', 'interest_arts', 'interest_policy', 'interest_design', 
    'interest_tech', 'interest_building', 'interest_nature', 'interest_detail',
    'interest_leading', 'interest_helping', 'interest_tools', 'interest_analysis',
    'interest_writing', 'interest_performing', 'interest_health_care', 'interest_finance',
    'interest_sales', 'interest_education', 'interest_management', 'interest_marketing',
    'interest_performing_arts', 'interest_counseling', 'interest_social_service', 
    'interest_legal', 'interest_business'
]

ALL_APTITUDES_DMGT = [
    'ability_logic', 'ability_creativity', 'ability_comm', 'ability_practical',
    'ability_teamwork', 'ability_spatial', 'ability_numerical', 'ability_abstract_reason',
    'ability_verbal_comp', 'ability_clerical', 'ability_mech_reason', 'ability_organization',
    'ability_detailcheck', 'ability_comprehension', 'ability_problem_solve',
    'dmgt_resilience', 'dmgt_persistence', 'dmgt_self_manage', 'dmgt_patience',
    'dmgt_flexibility', 'dmgt_integrity', 'dmgt_stress_manage', 'dmgt_initiative',
    'ability_comm_written', 'ability_negotiation'
]

# Combine for easy iteration
ALL_TRAITS = ALL_INTERESTS + ALL_APTITUDES_DMGT

# --- 2. COURSE DEFINITIONS & FIELD MAPPING (Retained from original) ---

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


# --- 3. BASELINE FIELD PROFILES (UPDATED FOR ALL 50 FIELDS) ---
# Structure: {'INTERESTS': {'trait_name': (low, high)}, 'APTITUDES_DMGT': {'trait_name': (low, high)}, 'SHS': 'strand'}

PROFILES_BY_FIELD = {
    'TECH': {
        'INTERESTS': {'interest_tech': (5,5), 'interest_research': (4,5), 'interest_analysis': (4,5), 'interest_building': (3,4), 'interest_design': (3,4)},
        'APTITUDES_DMGT': {'ability_logic': (5,5), 'ability_numerical': (4,5), 'ability_abstract_reason': (4,5), 'ability_detailcheck': (4,5), 'dmgt_persistence': (4,5)},
        'SHS': 'STEM'
    },
    'ENG': {
        'INTERESTS': {'interest_building': (5,5), 'interest_tools': (4,5), 'interest_research': (4,5), 'interest_tech': (3,4)},
        'APTITUDES_DMGT': {'ability_practical': (5,5), 'ability_logic': (5,5), 'ability_numerical': (4,5), 'ability_mech_reason': (5,5), 'ability_spatial': (4,5), 'ability_teamwork': (4,5)},
        'SHS': 'STEM'
    },
    'BUS': {
        'INTERESTS': {'interest_business': (5,5), 'interest_finance': (5,5), 'interest_leading': (4,5), 'interest_management': (5,5), 'interest_detail': (4,5)},
        'APTITUDES_DMGT': {'ability_logic': (4,5), 'ability_numerical': (4,5), 'ability_organization': (4,5), 'ability_comm': (3,4), 'dmgt_integrity': (4,5), 'ability_negotiation': (4,5)},
        'SHS': 'ABM'
    },
    'HEALTH': {
        'INTERESTS': {'interest_health_care': (5,5), 'interest_helping': (5,5), 'interest_research': (4,5), 'interest_nature': (3,4)},
        'APTITUDES_DMGT': {'ability_logic': (4,5), 'ability_verbal_comp': (4,5), 'ability_practical': (3,4), 'ability_detailcheck': (4,5), 'dmgt_patience': (5,5), 'dmgt_resilience': (4,5)},
        'SHS': 'STEM'
    },
    'SOCIAL': {
        'INTERESTS': {'interest_policy': (5,5), 'interest_research': (4,5), 'interest_helping': (4,5), 'interest_legal': (3,4)},
        'APTITUDES_DMGT': {'ability_comm': (5,5), 'ability_verbal_comp': (4,5), 'ability_logic': (3,4), 'ability_comprehension': (4,5), 'ability_teamwork': (4,5), 'dmgt_flexibility': (4,5)},
        'SHS': 'HUMSS'
    },
    'MEDIA': {
        'INTERESTS': {'interest_arts': (5,5), 'interest_design': (5,5), 'interest_writing': (5,5), 'interest_performing_arts': (4,5), 'interest_marketing': (4,5)},
        'APTITUDES_DMGT': {'ability_creativity': (5,5), 'ability_comm': (5,5), 'ability_comm_written': (4,5), 'ability_teamwork': (3,4), 'dmgt_initiative': (4,5)},
        'SHS': 'GAS'
    },
    'EDUC': {
        'INTERESTS': {'interest_education': (5,5), 'interest_helping': (4,5), 'interest_counseling': (4,5)},
        'APTITUDES_DMGT': {'ability_comm': (5,5), 'ability_teamwork': (5,5), 'dmgt_patience': (5,5), 'ability_creativity': (3,4), 'dmgt_self_manage': (4,5)},
        'SHS': 'HUMSS'
    },
    'PUB': {
        'INTERESTS': {'interest_policy': (5,5), 'interest_leading': (5,5), 'interest_social_service': (4,5), 'interest_helping': (4,5)},
        'APTITUDES_DMGT': {'ability_organization': (5,5), 'ability_comm': (4,5), 'ability_teamwork': (4,5), 'dmgt_integrity': (4,5), 'ability_logic': (4,5)},
        'SHS': 'HUMSS'
    },
    'HOSP': {
        'INTERESTS': {'interest_helping': (5,5), 'interest_management': (4,5), 'interest_business': (3,4)},
        'APTITUDES_DMGT': {'ability_teamwork': (5,5), 'ability_comm': (5,5), 'ability_practical': (4,5), 'ability_organization': (5,5), 'dmgt_stress_manage': (4,5)},
        'SHS': 'GAS'
    },
    'APPLIED': {
        'INTERESTS': {'interest_building': (5,5), 'interest_tools': (4,5), 'interest_tech': (4,5), 'interest_nature': (3,4)},
        'APTITUDES_DMGT': {'ability_practical': (5,5), 'ability_mech_reason': (5,5), 'ability_spatial': (4,5), 'ability_logic': (3,4)},
        'SHS': 'TVL'
    },
}

# --- 4. GENERATION LOGIC (Updated) ---

def generate_row_for_course(course):
    field_category = COURSE_TO_FIELD.get(course)
    if not field_category:
        return None
        
    profile = PROFILES_BY_FIELD[field_category]

    # Map SHS strand and set TVL strand
    strand = profile.get('SHS', 'GAS')
    tvl_strand = 'ICT' if strand == "TVL" else 'none'

    # Initialize row with core data and the new field_category
    row = {'shs_strand': strand, 'tvl_strand': tvl_strand, 'course': course, 'field_category': field_category}

    # Generate ratings for all 50 traits
    
    # 1. Interests (25)
    for i in ALL_INTERESTS:
        # Default to a middle-low range (1, 3) if not explicitly set in the field profile
        low, high = profile['INTERESTS'].get(i, (1, 3))
        row[i] = random.randint(low, high)
        
    # 2. Aptitudes & DMGT (25)
    for a in ALL_APTITUDES_DMGT:
        # Default to a middle-low range (1, 3) if not explicitly set in the field profile
        low, high = profile['APTITUDES_DMGT'].get(a, (1, 3))
        row[a] = random.randint(low, high)
        
    return row

if __name__ == "__main__":
    # --- Bias Mitigation Implemented Here: Equal rows per course ---
    NUM_ROWS_PER_COURSE = 60 # Set back to 60 for better training data size
    total_rows = len(COURSES) * NUM_ROWS_PER_COURSE
    
    print(f"Starting data generation for the expanded list of {len(COURSES)} courses.")
    print(f"Target: {NUM_ROWS_PER_COURSE} rows for each course. Total rows: {total_rows}.")
    
    all_data = []
    for course in COURSES:
        for _ in range(NUM_ROWS_PER_COURSE):
            all_data.append(generate_row_for_course(course))

    df = pd.DataFrame([data for data in all_data if data is not None])

    # Ensure all 50 columns are present, even if some rows didn't naturally generate them (fill missing with 1)
    for trait in ALL_TRAITS:
        if trait not in df.columns:
            df[trait] = 1 # Initialize missing columns

    # Shuffle the dataset to mix everything up
    df = df.sample(frac=1).reset_index(drop=True)
    
    output_path = 'courses_dataset.csv'
    df.to_csv(output_path, index=False)
    
    print("\n----------------------------------------------------")
    print(f"Successfully generated a balanced and massive dataset!")
    print(f"Saved {len(df)} rows to '{output_path}'.")
    print("----------------------------------------------------\n")
    print("NEXT STEP: You must run the data cleaning/combining script, and then re-train your models.")