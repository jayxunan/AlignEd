import pandas as pd
column_mapping = {
    'Which college course are you planning to choose?': 'course',
    'Select up to (3) courses you\'d consider choosing': 'considered_courses',
    'Current SHS Strand': 'shs_strand',
    'What is your current TVL Strand': 'tvl_strand',
    'Rate your interest in these areas (1-5)\n(1)least to (5)most interested [Science/Experiments]': 'interest_science',
    'Rate your interest in these areas (1-5)\n(1)least to (5)most interested [Arts/Writing]': 'interest_arts',
    'Rate your interest in these areas (1-5)\n(1)least to (5)most interested [Teaching/Tutoring]': 'interest_teaching',
    'Rate your interest in these areas (1-5)\n(1)least to (5)most interested [Business/Finance]': 'interest_business',
    'Rate your interest in these areas (1-5)\n(1)least to (5)most interested [Technology/Coding]': 'interest_tech',
    'Rate your interest in these areas (1-5)\n(1)least to (5)most interested [Graphic Design/Digital Arts]': 'interest_design',
    'Rate your interest in these areas (1-5)\n(1)least to (5)most interested [Physical Activity/Sports]': 'interest_sports',
    'Rate your abilities in these areas (1-5)\n(1)weak to (5)strong [Logical Thinking]': 'ability_logic',
    'Rate your abilities in these areas (1-5)\n(1)weak to (5)strong [Creativity]': 'ability_creativity',
    'Rate your abilities in these areas (1-5)\n(1)weak to (5)strong [Communication]': 'ability_comm',
    'Rate your abilities in these areas (1-5)\n(1)weak to (5)strong [Practical Skills (doing hands-on tasks, using tools)]': 'ability_practical',
    'Rate your abilities in these areas (1-5)\n(1)weak to (5)strong [Teamwork]': 'ability_teamwork'
}

try:
    df = pd.read_csv('Senior High School Course Interest Survey.csv')
    df.rename(columns=column_mapping, inplace=True)
    
    if 'course' not in df.columns or 'considered_courses' not in df.columns:
        raise KeyError("One of the course-related columns was not found after renaming. Please check your CSV file headers.")

    # pang fill
    df['course'].fillna(df['considered_courses'], inplace=True)

    # 1
    required_columns = [col for col in column_mapping.values() if col != 'considered_courses']
    df_clean = df[required_columns]

    # clean
    df_clean['course'] = df_clean['course'].apply(lambda x: str(x).split(';')[0].split(',')[0].strip())
    df_clean['tvl_strand'].fillna('none', inplace=True)
    df_clean.dropna(subset=['course'], inplace=True)
    df_clean = df_clean[df_clean['course'].str.lower().isin(['nan', '']) == False]

    df_clean.to_csv('courses_dataset.csv', index=False)
    
    print(f"✅ Successfully created 'courses_dataset.csv' with {len(df_clean)} rows.")
    print("➡️ Next step: Run 'python recommender/train_model.py'")

except FileNotFoundError:
    print("❌ Error: 'Senior High School Course Interest Survey.csv' not found.")
except KeyError as e:
    print(f"❌ Error: {e}")

