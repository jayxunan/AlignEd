import pandas as pd
import numpy as np
import random
import os

# (The PROFILES and COURSES lists are updated to include new interests)
PROFILES = {
    "STEM_Tech": {
        "interests": {"science": (5, 5), "tech": (5, 5), "building": (4, 5), "arts": (1, 2), "helping": (1, 2)},
        "abilities": {"logic": (5, 5), "practical": (3, 4), "comm": (2, 3)},
        "courses": ['Computer Science', 'Information Technology', 'Data Science', 'Web & Mobile App Development', 'Computer Engineering']
    },
    "STEM_Engineering": {
        "interests": {"science": (5, 5), "building": (5, 5), "tech": (4, 5), "arts": (1, 2)},
        "abilities": {"logic": (5, 5), "practical": (5, 5), "teamwork": (3, 4)},
        "courses": ['Civil Engineering', 'Mechanical Engineering', 'Electronics Engineering', 'Architecture']
    },
    "HUMSS_Social": {
        "interests": {"teaching": (5, 5), "helping": (4, 5), "leading": (4, 5), "arts": (3, 5), "science": (1, 2)},
        "abilities": {"comm": (5, 5), "creativity": (4, 5), "teamwork": (4, 5)},
        "courses": ['Psychology', 'Education (BEEd/BSEd)', 'Communication', 'Political Science', 'Public Administration', 'Social Work']
    },
    "ABM_Business": {
        "interests": {"business": (5, 5), "leading": (5, 5), "tech": (2, 4), "arts": (1, 2)},
        "abilities": {"comm": (4, 5), "teamwork": (5, 5), "logic": (3, 4)},
        "courses": ['Business Administration', 'Accountancy', 'Entrepreneurship', 'Marketing Management']
    },
    "TVL_Practical": {
        "interests": {"building": (5, 5), "tech": (4, 5), "sports": (3, 4), "arts": (1, 2)},
        "abilities": {"practical": (5, 5), "teamwork": (4, 5), "logic": (3, 4)},
        "courses": ['ICT (Tech-Voc)', 'Automotive Technology', 'Electrical Installation', 'Welding Technology']
    },
     "Health_Sciences": {
        "interests": {"science": (5, 5), "helping": (5, 5), "teaching": (3, 4), "tech": (1, 2)},
        "abilities": {"logic": (4, 5), "comm": (4, 5), "practical": (4, 5)},
        "courses": ['Nursing', 'Medical Technology', 'Pharmacy', 'Physical Therapy', 'Biology']
    },
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

        row = {'shs_strand': strand, 'tvl_strand': 'ICT' if strand == "TVL" else 'none', 'course': random.choice(profile['courses'])}
        
        # Define all possible interests and abilities
        interests = ['science', 'arts', 'teaching', 'business', 'tech', 'design', 'sports', 'building', 'nature', 'leading', 'helping']
        abilities = ['logic', 'creativity', 'comm', 'practical', 'teamwork']

        for i in interests:
            low, high = profile['interests'].get(i, (1, 3)) # Default to a middle-low range
            row[f'interest_{i}'] = random.randint(low, high)
        for a in abilities:
            low, high = profile['abilities'].get(a, (1, 3))
            row[f'ability_{a}'] = random.randint(low, high)
        data.append(row)
    
    return pd.DataFrame(data)

if __name__ == '__main__':
    print("Generating 150 simulated student responses with new, specific interests...")
    simulated_df = generate_simulated_data(150)
    
    cleaned_real_data_path = 'courses_dataset.csv'
    
    if os.path.exists(cleaned_real_data_path):
        try:
            real_df = pd.read_csv(cleaned_real_data_path)
            print(f"Found {len(real_df)} real survey responses. Combining with simulated data.")
            # Ensure real_df has all the new columns, filling missing with 0
            for col in simulated_df.columns:
                if col not in real_df.columns:
                    real_df[col] = 0
            combined_df = pd.concat([real_df, simulated_df], ignore_index=True)
        except pd.errors.EmptyDataError:
            print("Real survey data file is empty. Using only simulated data.")
            combined_df = simulated_df
    else:
        print("No existing survey data found. Using only simulated data.")
        combined_df = simulated_df

    combined_df = combined_df[simulated_df.columns] # Ensure consistent column order
    combined_df.to_csv(cleaned_real_data_path, index=False)
    
    print(f"\n✅ Successfully updated '{cleaned_real_data_path}' with {len(combined_df)} total rows.")
    print("➡️ Next Step: Run 'python recommender/train_model.py' to give your AI a new brain!")