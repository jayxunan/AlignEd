# recommender/management/commands/seed_university_data.py

from django.core.management.base import BaseCommand
from recommender.models import Course, University
from django.db import transaction
import os

# --- 1. Define the 12 Universities (University Model Data) ---
UNIVERSITY_LIST = [
    "University of the Philippines (UP)",
    "De La Salle University (DLSU)",
    "University of Santo Tomas (UST)",
    "Polytechnic University of the Philippines (PUP)",
    "Mapúa University",
    "Adamson University",
    "Lyceum of the Philippines University (LPU)",
    "University of the East (UE)",
    "Far Eastern University (FEU)",
    "Philippine Normal University (PNU)",
    "Technological University of the Philippines (TUP)",
    "STI College",
]

# --- 2. Define Final Cleaned Courses and their Field/University Mapping ---
# The list has been adjusted to use the final 85 names provided.
COURSE_DATA = {
    # -----------------------------------------------------
    # TECH (T) - High Logic, Tech, Detail
    # -----------------------------------------------------
    'Computer Science': ('TECH', ['UP', 'DLSU', 'UST', 'PUP', 'UE', 'LPU', 'STI']),
    'Information Technology': ('TECH', ['DLSU', 'UST', 'PUP', 'UE', 'LPU', 'STI', 'TUP']),
    'Information Systems': ('TECH', ['DLSU', 'Adamson', 'TUP']),
    'Information Security': ('TECH', ['DLSU', 'LPU']),
    'Web & Mobile Development': ('TECH', ['UST']),
    'Game Design & Development': ('TECH', ['UST', 'LPU']),
    'Data Science & Analytics': ('TECH', ['DLSU', 'FEU', 'LPU']),
    'Data Science': ('TECH', ['DLSU']), # Kept separate for clarity
    'Actuarial Science': ('TECH', ['UST', 'DLSU']),
    'Business Analytics': ('TECH', ['UST', 'DLSU']),
    'Applied Mathematics': ('TECH', ['UP', 'PUP', 'FEU', 'PNU']),
    
    # -----------------------------------------------------
    # ENG/ARCH (E) - High Spatial, Building, Practical
    # -----------------------------------------------------
    'Architecture': ('ENG', ['UP', 'UST', 'PUP', 'Mapúa', 'Adamson', 'UE', 'FEU', 'TUP']),
    'Interior Design': ('ENG', ['UP', 'UST', 'Mapúa', 'UE']),
    'Manufacturing & Robotics Engineering': ('ENG', ['DLSU', 'Mapúa']),
    'Metallurgical Engineering': ('ENG', ['UP', 'UST']),
    'Mechatronics': ('ENG', ['DLSU', 'Mapúa']),
    'Construction Engineering & Management': ('ENG', ['UST', 'Mapúa']),
    'Transportation Engineering': ('ENG', ['UST']),
    'Civil Engineering': ('ENG', ['UP', 'DLSU', 'UST', 'PUP', 'Mapúa', 'Adamson', 'UE', 'TUP']),
    'Computer Engineering': ('ENG', ['UP', 'DLSU', 'UST', 'PUP', 'Mapúa', 'Adamson', 'UE', 'STI', 'TUP']),
    'Electrical Engineering': ('ENG', ['UP', 'DLSU', 'UST', 'PUP', 'Mapúa', 'Adamson', 'UE', 'TUP']),
    'Instrumentation & Control Engineering': ('ENG', ['UST', 'TUP']),
    'Industrial Engineering': ('ENG', ['UP', 'DLSU', 'UST', 'PUP', 'Mapúa', 'Adamson']),
    'Biological Engineering': ('ENG', ['Mapúa']),
    
    # -----------------------------------------------------
    # HEALTH/SCIENCE (H) - High Research, Science, Helping
    # -----------------------------------------------------
    'Medicine': ('HEALTH', ['UST']), 
    'Dentistry': ('HEALTH', ['UST']), 
    'Nursing': ('HEALTH', ['UP', 'UST', 'Adamson', 'FEU']),
    'Medical Technology': ('HEALTH', ['UST', 'FEU']),
    'Pharmaceutical Sciences': ('HEALTH', ['UST', 'Adamson', 'FEU']),
    'Nutrition & Dietetics': ('HEALTH', ['UP', 'PUP', 'UST', 'FEU', 'PNU']),
    'Clinical Audiology': ('HEALTH', ['UST']),
    'Clinical Pharmacy': ('HEALTH', ['UST']),
    'Health Professions': ('HEALTH', ['UST']), # Used for general BSHS, PT, OT, SLP
    'Human Biology': ('HEALTH', ['DLSU']),
    'Biology': ('HEALTH', ['UP', 'PUP', 'DLSU', 'UST', 'Adamson', 'FEU', 'PNU']),
    'Biochemistry': ('HEALTH', ['DLSU', 'UST', 'Adamson', 'FEU']),
    'Biotechnology': ('HEALTH', ['DLSU']),
    'Chemistry': ('HEALTH', ['UP', 'PUP', 'DLSU', 'UST', 'Mapúa', 'Adamson', 'FEU', 'PNU']),
    'Physics': ('HEALTH', ['UP', 'PUP', 'DLSU', 'UST', 'Mapúa', 'PNU']),
    'Zoology / Systematics & Ecology': ('HEALTH', ['DLSU']),
    'Veterinary or Animal Sciences': ('HEALTH', ['DLSU']),
    'Applied Science — Laboratory Technology (BAS-LT)': ('HEALTH', ['TUP']),

    # -----------------------------------------------------
    # BUSINESS/ECON (B) - High Business, Leading, Detail
    # -----------------------------------------------------
    'Accountancy': ('BUS', ['UP', 'DLSU', 'UST', 'PUP', 'Adamson', 'UE', 'FEU', 'STI']),
    'Internal Auditing': ('BUS', ['FEU']),
    'Business Administration': ('BUS', ['UP', 'DLSU', 'UST', 'PUP', 'Adamson', 'UE', 'FEU', 'LPU', 'STI', 'TUP']),
    'Entrepreneurship': ('BUS', ['DLSU', 'UST', 'PUP', 'FEU', 'TUP']),
    'Financial Management': ('BUS', ['UST', 'PUP', 'Adamson', 'FEU']),
    'Marketing Management': ('BUS', ['DLSU', 'UST', 'PUP', 'Adamson', 'FEU', 'LPU']),
    'Operations Management (Business major)': ('BUS', ['Adamson', 'LPU']),
    'Applied Corporate Management': ('BUS', ['DLSU']),
    'Business Economics': ('BUS', ['UP', 'DLSU', 'UST', 'FEU']),
    'Economics': ('BUS', ['UP', 'DLSU', 'UST', 'PUP']),
    'Real Estate': ('BUS', ['UST']),
    'Legal Studies (Law)': ('BUS', ['DLSU', 'UST', 'LPU']),
    
    # -----------------------------------------------------
    # SOCIAL/HUMANITIES (S) - High Policy, Helping, Comm
    # -----------------------------------------------------
    'Psychology': ('SOCIAL', ['UP', 'DLSU', 'UST', 'PUP', 'Adamson', 'UE', 'FEU', 'PNU', 'LPU']),
    'Political Science': ('SOCIAL', ['UP', 'DLSU', 'UST', 'PUP', 'Adamson', 'FEU']),
    'International Studies': ('SOCIAL', ['UP', 'DLSU', 'PUP', 'FEU', 'LPU']),
    'Philippine Studies': ('SOCIAL', ['UP', 'DLSU', 'FEU']),
    'Asian Studies': ('SOCIAL', ['UST']),
    'Linguistics': ('SOCIAL', ['UP']),
    'Social Sciences': ('SOCIAL', ['DLSU', 'UST', 'PUP']),
    'Community Development': ('SOCIAL', ['UP', 'PUP']),
    'Archaeology / Archaeological Studies': ('SOCIAL', ['UP']),
    'Clinical Psychology': ('SOCIAL', ['UST', 'Adamson']),
    
    # -----------------------------------------------------
    # MEDIA/ARTS (M) - High Creativity, Arts, Design
    # -----------------------------------------------------
    'Broadcasting': ('MEDIA', ['UP', 'PUP', 'LPU']),
    'Journalism': ('MEDIA', ['UP', 'PUP', 'LPU']),
    'Advertising': ('MEDIA', ['DLSU', 'UST']),
    'Digital Film & Media Production': ('MEDIA', ['FEU']),
    'Multimedia Arts': ('MEDIA', ['LPU', 'UE', 'STI']),
    'Arts': ('MEDIA', ['UP', 'UST', 'UE', 'FEU', 'TUP']),
    'Theatre & Performance': ('MEDIA', ['UP', 'PUP', 'UST']),
    'Creative Writing': ('MEDIA', ['UP', 'DLSU', 'UST']),
    'Mass Communication': ('MEDIA', ['DLSU', 'Adamson', 'LPU', 'UE', 'FEU']),
    'Organizational Communication': ('MEDIA', ['DLSU']),
    'Voice & Vocal Performance': ('MEDIA', ['UST']),
    
    # -----------------------------------------------------
    # EDUCATION (D) - High Teaching, Helping, Comm
    # -----------------------------------------------------
    'Education': ('EDUC', ['UP', 'PUP', 'DLSU', 'UST', 'Adamson', 'FEU', 'PNU', 'TUP']),
    'Art Education': ('EDUC', ['UP', 'PNU']),
    'Fitness & Sports Management': ('EDUC', ['UST', 'Adamson', 'FEU', 'TUP']),
    
    # -----------------------------------------------------
    # HOSPITALITY/APPLIED (A) - High Practical, Building, Helping
    # -----------------------------------------------------
    'Public Administration': ('PUB', ['UP', 'UST', 'PUP']),
    'Tourism Management': ('HOSP', ['UST', 'PUP', 'UE', 'FEU', 'STI']),
    'Hotel, Restaurant & Institutional Management': ('HOSP', ['UP', 'UST', 'PUP', 'Adamson', 'LPU', 'TUP']),
    'Cruise Line Operations': ('HOSP', ['LPU', 'FEU']),
    'Criminology': ('APPLIED', ['LPU']),
    'Forensic': ('APPLIED', ['UST']),
    'Marine / Maritime-related': ('APPLIED', ['PUP']),
    'Vehicle/Automotive Engineering Technology': ('APPLIED', ['TUP']),
    'Apparel and Fashion Technology': ('APPLIED', ['TUP']),
    'Industrial Arts': ('APPLIED', ['PUP', 'TUP']),
}

class Command(BaseCommand):
    help = 'Seeds the database with final University and Course data, and links them.'

    def handle(self, *args, **options):
        # A map to convert short university codes to their full name for linking
        # This helper map is essential for reliable lookups
        UNI_CODE_MAP = {
            "UP": "University of the Philippines (UP)",
            "DLSU": "De La Salle University (DLSU)",
            "UST": "University of Santo Tomas (UST)",
            "PUP": "Polytechnic University of the Philippines (PUP)",
            "Mapúa": "Mapúa University",
            "Adamson": "Adamson University",
            "LPU": "Lyceum of the Philippines University (LPU)",
            "UE": "University of the East (UE)",
            "FEU": "Far Eastern University (FEU)",
            "PNU": "Philippine Normal University (PNU)",
            "TUP": "Technological University of the Philippines (TUP)",
            "STI": "STI College",
        }
        
        self.stdout.write(self.style.NOTICE("--- Starting FINAL Database Seeding for AlignEd ---"))

        try:
            with transaction.atomic():
                # --- 1. Seed Universities ---
                self.stdout.write("1. Seeding Universities...")
                uni_objects = {}
                for code, uni_name in UNI_CODE_MAP.items():
                    uni, created = University.objects.get_or_create(name=uni_name)
                    uni_objects[code] = uni 
                
                self.stdout.write(self.style.SUCCESS(f"   -> {len(uni_objects)} Universities confirmed."))

                # --- 2. Seed Courses and Link to Universities ---
                self.stdout.write("\n2. Seeding FINAL Courses and creating links...")
                courses_added = 0
                links_created = 0

                # Clear existing course data first to ensure we only have the final ~85 courses
                Course.objects.all().delete()
                
                for course_name, (field_code, uni_codes) in COURSE_DATA.items():
                    # Create the Course object
                    course, created = Course.objects.get_or_create(
                        name=course_name,
                        defaults={
                            'field_category': field_code,
                            # Simple generic description based on field
                            'description': f"A major program emphasizing core concepts and professional application in the field of {course_name} (Category: {field_code}).",
                            'icon': 'book-open' 
                        }
                    )
                    
                    if created:
                        courses_added += 1
                    
                    # Link the Course to the Universities
                    course.offering_universities.clear() 
                    
                    for uni_code in uni_codes:
                        if uni_code in uni_objects:
                            course.offering_universities.add(uni_objects[uni_code])
                            links_created += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"   -> WARNING: University code '{uni_code}' not found for {course_name}."))

                self.stdout.write(self.style.SUCCESS(f"   -> Courses processed: {len(COURSE_DATA)}"))
                self.stdout.write(self.style.SUCCESS(f"   -> New courses added: {courses_added}"))
                self.stdout.write(self.style.SUCCESS(f"   -> Total links created: {links_created}"))

                self.stdout.write(self.style.SUCCESS("\nDatabase seeding complete!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred during seeding: {e}"))