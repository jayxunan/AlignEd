from django.core.management.base import BaseCommand
from recommender.models import Course

class Command(BaseCommand):
    help = 'Populates the database with the expanded and balanced list of courses.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting existing courses to ensure a clean update...")
        Course.objects.all().delete()

        # The expanded and balanced list now contains 36 courses.
        courses_to_add = [
            # --- Technology & Computing ---
            {'name': 'Computer Science', 'description': 'Focuses on algorithms, data structures, and the theory of computation to build complex software.', 'icon': 'cpu'},
            {'name': 'Information Technology', 'description': 'A practical approach to computing, focusing on software development, networks, and systems.', 'icon': 'server'},
            {'name': 'Data Science', 'description': 'Combines statistics and computer science to extract insights and knowledge from data.', 'icon': 'bar-chart-2'},
            {'name': 'Game Development', 'description': 'A specialized field focusing on the design, development, and production of video games.', 'icon': 'target'},
            {'name': 'Web & Mobile App Development', 'description': 'A focused track on creating applications for websites, iOS, and Android platforms.', 'icon': 'smartphone'}, # NEW
            {'name': 'ICT (Tech-Voc)', 'description': 'A technical-vocational track focusing on practical skills in information technology.', 'icon': 'tool'},

            # --- Engineering & Architecture ---
            {'name': 'Computer Engineering', 'description': 'Blends electrical engineering and computer science to design and develop computer hardware.', 'icon': 'git-branch'},
            {'name': 'Civil Engineering', 'description': 'Involves the design and construction of infrastructure projects like roads and bridges.', 'icon': 'home'},
            {'name': 'Electronics Engineering', 'description': 'Deals with the design of electronic circuits, devices, and systems for various applications.', 'icon': 'radio'},
            {'name': 'Mechanical Engineering', 'description': 'Focuses on the design, analysis, and manufacturing of mechanical systems.', 'icon': 'settings'},
            {'name': 'Architecture', 'description': 'The art and science of designing buildings and other physical structures.', 'icon': 'triangle'},

            # --- Health Sciences ---
            {'name': 'Nursing', 'description': 'A healthcare profession focused on the care of individuals, families, and communities.', 'icon': 'heart'},
            {'name': 'Medical Technology', 'description': 'Involves performing laboratory analysis used in the diagnosis and treatment of disease.', 'icon': 'activity'},
            {'name': 'Pharmacy', 'description': 'The science and practice of preparing, dispensing, and reviewing drugs and providing additional clinical services.', 'icon': 'droplet'},
            {'name': 'Physical Therapy', 'description': 'A healthcare profession that helps patients recover from injury, illness, and surgery.', 'icon': 'user-check'},
            {'name': 'Biology', 'description': 'The study of living organisms, divided into many specialized fields that cover their morphology and physiology.', 'icon': 'wind'},

            # --- Business & Management ---
            {'name': 'Business Administration', 'description': 'Develops skills in management, finance, marketing, and human resources.', 'icon': 'briefcase'},
            {'name': 'Accountancy', 'description': 'The practice of recording, classifying, and reporting on business transactions.', 'icon': 'book-open'},
            {'name': 'Entrepreneurship', 'description': 'Focuses on the process of designing, launching, and running a new business.', 'icon': 'trending-up'},
            {'name': 'Marketing Management', 'description': 'Focuses on the practical application of marketing techniques and the management of a firm\'s marketing resources.', 'icon': 'shopping-bag'},

            # --- Social Sciences & Humanities ---
            {'name': 'Psychology', 'description': 'The scientific study of the mind and behavior, exploring both conscious and unconscious phenomena.', 'icon': 'message-circle'},
            {'name': 'Communication', 'description': 'The study of how humans create, transmit, and receive messages to influence one another.', 'icon': 'message-square'},
            {'name': 'Criminology', 'description': 'The scientific study of the nature, extent, and causes of criminal behavior.', 'icon': 'shield'},
            {'name': 'Public Administration', 'description': 'Focuses on the management of government agencies and the implementation of public policy.', 'icon': 'flag'},
            {'name': 'Political Science', 'description': 'The study of politics and power from domestic, international, and comparative perspectives.', 'icon': 'globe'},
            {'name': 'Social Work', 'description': 'A practice-based profession that promotes social change, development, and the well-being of people.', 'icon': 'users'},

            # --- Creative Arts ---
            {'name': 'Multimedia Arts', 'description': 'Integrates various artistic media, such as art, design, video, and sound.', 'icon': 'camera'},
            {'name': 'Industrial Design', 'description': 'The professional practice of designing products used by millions of people around the world every day.', 'icon': 'pen-tool'},

            # --- Education ---
            {'name': 'Education (BEEd/BSEd)', 'description': 'Prepares students for a career in teaching at the elementary or secondary level.', 'icon': 'award'},

            # --- Service Industries ---
            {'name': 'Hospitality Management', 'description': 'Focuses on the management of hotels, restaurants, and other hospitality services.', 'icon': 'coffee'},
            {'name': 'Tourism Management', 'description': 'Covers the management of all activities, services, and industries related to tourism.', 'icon': 'map-pin'},

            # --- Technical-Vocational ---
            {'name': 'Automotive Technology', 'description': 'A vocational program preparing students for careers as automotive service technicians.', 'icon': 'truck'},
            {'name': 'Electrical Installation', 'description': 'A technical program focusing on the installation and maintenance of electrical systems.', 'icon': 'power'},
            
            # --- Agriculture & Sciences ---
            {'name': 'Agriculture', 'description': 'The science and art of cultivating plants and livestock for food and other products.', 'icon': 'feather'},
            {'name': 'Marine Biology', 'description': 'The scientific study of organisms in the ocean or other marine or brackish bodies of water.', 'icon': 'anchor'},
        ]

        self.stdout.write(f"Populating database with {len(courses_to_add)} new courses...")
        for course_data in courses_to_add:
            Course.objects.create(
                name=course_data['name'],
                description=course_data['description'],
                icon=course_data['icon']
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully populated the database with {len(courses_to_add)} courses.'))

