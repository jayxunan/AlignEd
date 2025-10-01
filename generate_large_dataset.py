import pandas as pd
import numpy as np
import random

# --- COMPLETE LIST OF 35 COURSES ---
COURSES = [
    'Computer Science', 'Information Technology', 'Data Science', 'Game Development', 'Web & Mobile App Development', 'ICT (Tech-Voc)',
    'Computer Engineering', 'Civil Engineering', 'Electronics Engineering', 'Mechanical Engineering', 'Architecture',
    'Nursing', 'Medical Technology', 'Pharmacy', 'Physical Therapy', 'Biology',
    'Business Administration', 'Accountancy', 'Entrepreneurship', 'Marketing Management',
    'Psychology', 'Communication', 'Criminology', 'Public Administration', 'Political Science', 'Social Work',
    'Multimedia Arts', 'Industrial Design', 'Education (BEEd/BSEd)', 'Hospitality Management', 'Tourism Management',
    'Automotive Technology', 'Electrical Installation', 'Mechatronics Technology', 'Agriculture', 'Marine Biology'
]

# --- DETAILED PERSONAS FOR DATA GENERATION ---
PROFILES = {
    'Tech': {'interests': {'tech': (5,5), 'building': (4,5), 'science': (3,4)}, 'abilities': {'logic': (5,5), 'practical': (4,5)}, 'courses': ['Computer Science', 'Information Technology', 'Data Science', 'Web & Mobile App Development', 'ICT (Tech-Voc)']},
    'Engineering': {'interests': {'building': (5,5), 'science': (4,5), 'tech': (3,4)}, 'abilities': {'logic': (5,5), 'practical': (5,5)}, 'courses': ['Computer Engineering', 'Civil Engineering', 'Electronics Engineering', 'Mechanical Engineering']},
    'Architecture': {'interests': {'design': (5,5), 'arts': (4,5), 'building': (3,4)}, 'abilities': {'creativity': (5,5), 'logic': (4,5)}, 'courses': ['Architecture']},
    'Health': {'interests': {'helping': (5,5), 'science': (5,5), 'teaching': (3,4)}, 'abilities': {'comm': (4,5), 'logic': (4,5)}, 'courses': ['Nursing', 'Medical Technology', 'Pharmacy', 'Physical Therapy']},
    'Sciences': {'interests': {'science': (5,5), 'nature': (4,5), 'tech': (2,3)}, 'abilities': {'logic': (5,5), 'practical': (3,4)}, 'courses': ['Biology', 'Marine Biology', 'Agriculture']},
    'Business': {'interests': {'business': (5,5), 'leading': (5,5), 'tech': (2,3)}, 'abilities': {'comm': (5,5), 'teamwork': (4,5)}, 'courses': ['Business Administration', 'Accountancy', 'Entrepreneurship', 'Marketing Management']},
    'Social & Humanities': {'interests': {'helping': (5,5), 'teaching': (4,5), 'arts': (4,5)}, 'abilities': {'comm': (5,5), 'creativity': (4,5)}, 'courses': ['Psychology', 'Communication', 'Criminology', 'Public Administration', 'Political Science', 'Social Work', 'Education (BEEd/BSEd)']},
    'Creative Arts': {'interests': {'arts': (5,5), 'design': (5,5), 'tech': (2,4)}, 'abilities': {'creativity': (5,5), 'practical': (3,4)}, 'courses': ['Multimedia Arts', 'Industrial Design', 'Game Development']},
    'Services': {'interests': {'helping': (5,5), 'leading': (4,5), 'business': (3,4)}, 'abilities': {'teamwork': (5,5), 'comm': (5,5)}, 'courses': ['Hospitality Management', 'Tourism Management']},
    'Vocational': {'interests': {'building': (5,5), 'tech': (4,5), 'sports': (2,3)}, 'abilities': {'practical': (5,5), 'logic': (3,4)}, 'courses': ['Automotive Technology', 'Electrical Installation', 'Mechatronics Technology']},
}

# Reverse map to find a persona for any given course
COURSE_TO_PROFILE = {course: profile_name for profile_name, details in PROFILES.items() for course in details['courses']}

def generate_row_for_course(course):
    profile_name = COURSE_TO_PROFILE.get(course)
    if not profile_name:
        return None # Should not happen if all courses are mapped
    
    profile = PROFILES[profile_name]

    if "STEM" in course or "Engineering" in course or "Science" in course: strand = "STEM"
    elif "Business" in course or "Accountancy" in course or "Marketing" in course: strand = "ABM"
    elif "Psychology" in course or "Communication" in course or "Education" in course: strand = "HUMSS"
    elif "Vocational" in course or "Tech-Voc" in course or "Technology" in course: strand = "TVL"
    else: strand = "GAS"

    row = {'shs_strand': strand, 'tvl_strand': 'ICT' if strand == "TVL" else 'none', 'course': course}

    all_interests = ['science', 'arts', 'teaching', 'business', 'tech', 'design', 'sports', 'building', 'nature', 'leading', 'helping']
    all_abilities = ['logic', 'creativity', 'comm', 'practical', 'teamwork']

    for i in all_interests:
        low, high = profile['interests'].get(i, (1, 3))
        row[f'interest_{i}'] = random.randint(low, high)
    for a in all_abilities:
        low, high = profile['abilities'].get(a, (1, 3))
        row[f'ability_{a}'] = random.randint(low, high)
        
    return row

if __name__ == "__main__":
    NUM_ROWS_PER_COURSE = 60
    total_rows = len(COURSES) * NUM_ROWS_PER_COURSE
    
    print(f"Starting data generation...")
    print(f"Target: {NUM_ROWS_PER_COURSE} rows for each of the {len(COURSES)} courses.")
    print(f"Total rows to be generated: {total_rows}")
    
    all_data = []
    for course in COURSES:
        for _ in range(NUM_ROWS_PER_COURSE):
            all_data.append(generate_row_for_course(course))

    df = pd.DataFrame(all_data)

    # Shuffle the dataset to mix everything up
    df = df.sample(frac=1).reset_index(drop=True)
    
    output_path = 'courses_dataset.csv'
    df.to_csv(output_path, index=False)
    
    print("\n----------------------------------------------------")
    print(f"✅ Successfully generated a new, balanced dataset!")
    print(f"✅ Saved {len(df)} rows to '{output_path}'.")
    print("----------------------------------------------------\n")
    print("➡️ Your system is now ready to be trained with high-quality, unbiased data.")
    print("➡️ Next Step: Run 'python recommender/train_model.py' to give your AI its new brain.")