from django.core.management.base import BaseCommand
from recommender.models import Course, University
from django.db import transaction
import os

# --- 1. Define the 12 Universities (University Model Data) ---
UNIVERSITY_LIST = [
    "University of the Philippines (UP)", "De La Salle University (DLSU)", 
    "University of Santo Tomas (UST)", "Polytechnic University of the Philippines (PUP)",
    "Mapúa University", "Adamson University", "Lyceum of the Philippines University (LPU)",
    "University of the East (UE)", "Far Eastern University (FEU)", 
    "Philippine Normal University (PNU)", "Technological University of the Philippines (TUP)",
    "STI College",
]

# --- NEW: Descriptive text for universities ---
UNI_DESCRIPTIONS = {
    "University of the Philippines (UP)": "The national university, known for academic excellence, extensive research, and public service. Admission is highly competitive via the UPCAT or a combination of GWA/tests. Tuition is generally free or heavily subsidized.",
    "De La Salle University (DLSU)": "A leading private Catholic institution specializing in engineering, business, and computer science. Known for its rigorous academic standards and strong research output.",
    "University of Santo Tomas (UST)": "The oldest university in Asia, offering strong programs in medicine, architecture, and the liberal arts. Known for its large campus and cultural heritage.",
    "Polytechnic University of the Philippines (PUP)": "A public, non-sectarian university known for affordable tuition and strong programs in engineering, accountancy, and business. Highly accessible and one of the largest student bodies.",
    "Mapúa University": "A premiere technological university famous for its engineering and IT programs. Known for its quarterm system and focus on hands-on technical education.",
    "Adamson University": "A Catholic university known for its programs in engineering, sciences, and business. Offers competitive admission standards and a wide range of degrees.",
    "Lyceum of the Philippines University (LPU)": "Known primarily for its excellent programs in hospitality, tourism, and communication arts. A dynamic private institution with a growing presence.",
    "University of the East (UE)": "Offers robust programs in Accountancy, Business, and Computer Studies. A large private university known for accessible education.",
    "Far Eastern University (FEU)": "Known for its distinguished programs in business, nursing, and architecture. Offers a mix of modern and historical architecture on its Manila campus.",
    "Philippine Normal University (PNU)": "The center for teacher education and specialized courses in education and arts. Highly regarded for training future educators.",
    "Technological University of the Philippines (TUP)": "A state university focused entirely on technological education and applied arts. Provides practical and hands-on skills training.",
    "STI College": "A private college chain focusing on IT, business administration, and hospitality management. Known for technology-driven education and quick industry integration.",
}
# --- 2. Define Final Cleaned Courses and their Field/University Mapping ---
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
    'Data Science': ('TECH', ['DLSU']),
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
    
    # FIX: Restoring generic entry that covers BSHS/PT/OT to stabilize count
    'Health Professions': ('HEALTH', ['UST', 'DLSU', 'UP', 'FEU']), # Consolidated entry (PT/OT/BSHS)
    
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
        UNI_CODE_MAP = {
            "UP": "University of the Philippines (UP)", "DLSU": "De La Salle University (DLSU)",
            "UST": "University of Santo Tomas (UST)", "PUP": "Polytechnic University of the Philippines (PUP)",
            "Mapúa": "Mapúa University", "Adamson": "Adamson University", 
            "LPU": "Lyceum of the Philippines University (LPU)", "UE": "University of the East (UE)",
            "FEU": "Far Eastern University (FEU)", "PNU": "Philippine Normal University (PNU)", 
            "TUP": "Technological University of the Philippines (TUP)", "STI": "STI College",
        }
        
        self.stdout.write(self.style.NOTICE("--- Starting FINAL Database Seeding for AlignEd ---"))

        try:
            with transaction.atomic():
                # --- 1. Seed Universities ---
                self.stdout.write("1. Seeding Universities...")
                uni_objects = {}
                for code, uni_name in UNI_CODE_MAP.items():
                    # FIX: Use update_or_create to set the description on every run
                    uni, created = University.objects.update_or_create(
                        name=uni_name,
                        defaults={
                            'description': UNI_DESCRIPTIONS.get(uni_name, "No detailed information available for this university.") 
                        }
                    )
                    uni_objects[code] = uni 
                
                self.stdout.write(self.style.SUCCESS(f"    -> {len(uni_objects)} Universities confirmed and updated."))

                self.stdout.write("\n2. Seeding FINAL Courses and creating links...")
                courses_added = 0
                links_created = 0

                Course.objects.all().delete()
                
                for course_name, (field_code, uni_codes) in COURSE_DATA.items():
                    course, created = Course.objects.get_or_create(
                        name=course_name,
                        defaults={
                            'field_category': field_code,
                            'description': f"A major program emphasizing core concepts and professional application in the field of {course_name} (Category: {field_code}).",
                            'icon': 'book-open' 
                        }
                    )
                    
                    if created:
                        courses_added += 1
                    
                    course.offering_universities.clear() 
                    
                    for uni_code in uni_codes:
                        if uni_code in uni_objects:
                            course.offering_universities.add(uni_objects[uni_code])
                            links_created += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"    -> WARNING: University code '{uni_code}' not found for {course_name}."))

                self.stdout.write(self.style.SUCCESS(f"    -> Courses processed: {len(COURSE_DATA)}"))
                self.stdout.write(self.style.SUCCESS(f"    -> New courses added: {courses_added}"))
                self.stdout.write(self.style.SUCCESS(f"    -> Total links created: {links_created}"))

                self.stdout.write(self.style.SUCCESS("\nDatabase seeding complete!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred during seeding: {e}"))