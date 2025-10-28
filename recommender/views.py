from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import random
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse, FileResponse, Http404, HttpResponseServerError
import os
import json
import csv
from .models import Assessment, Course, University, PersonaTemplate, CoursePersonaWeight
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import joblib 
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
FIELD_MODEL_PATH = os.path.join(BASE_DIR, 'field_model.joblib')
ENCODERS_PATH = os.path.join(BASE_DIR, 'label_encoders.joblib')

# Global variables to hold the loaded models
FIELD_MODEL = None
ENCODERS = None

try:
    # 1. Load the models only ONCE
    FIELD_MODEL = joblib.load(FIELD_MODEL_PATH)
    ENCODERS = joblib.load(ENCODERS_PATH)
    print("SUCCESS: ML Models and Encoders loaded successfully at startup.")
except Exception as e:
    # Print error to logs if model fails to load
    print(f"CRITICAL ERROR: Failed to load ML models: {e}")
    # The application will still start, but the view will now fail gracefully.

COURSE_PERSONAS = {
    # -----------------------------------------------------
    # TECHNOLOGY, COMPUTING, & DATA
    # -----------------------------------------------------
    'Computer Science': {'key_traits': ['ability_logic', 'interest_tech', 'interest_research'], 'label': 'Logical Systems Builder', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'interest_research': 4, 'ability_creativity': 3, 'ability_practical': 4}},
    'Information Technology': {'key_traits': ['ability_practical', 'interest_tech', 'ability_teamwork'], 'label': 'Practical Technologist', 'profile': {'ability_practical': 5, 'interest_tech': 5, 'ability_teamwork': 4, 'ability_comm': 3, 'interest_building': 4}},
    'Information Systems': {'key_traits': ['interest_detail', 'ability_logic', 'interest_business'], 'label': 'Tech-Business Integrator', 'profile': {'interest_detail': 5, 'ability_logic': 4, 'interest_business': 4, 'interest_tech': 4, 'ability_teamwork': 3}},
    'Information Security': {'key_traits': ['ability_logic', 'interest_tech', 'interest_detail'], 'label': 'Digital Defender', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'interest_detail': 4, 'ability_practical': 3, 'interest_leading': 3}},
    'Web & Mobile Development': {'key_traits': ['ability_creativity', 'ability_practical', 'interest_design'], 'label': 'Creative Developer', 'profile': {'ability_creativity': 5, 'ability_practical': 5, 'interest_design': 4, 'interest_tech': 5, 'ability_logic': 3}},
    'Game Design & Development': {'key_traits': ['ability_creativity', 'ability_logic', 'interest_design'], 'label': 'Interactive Designer', 'profile': {'ability_creativity': 5, 'ability_logic': 4, 'interest_design': 5, 'interest_arts': 4, 'interest_tech': 4}},
    'Data Science & Analytics': {'key_traits': ['ability_logic', 'interest_research', 'interest_detail'], 'label': 'Analytical Specialist', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_detail': 4, 'interest_tech': 4, 'ability_comm': 3}},
    'Business Analytics': {'key_traits': ['interest_business', 'ability_logic', 'interest_detail'], 'label': 'Business Strategist', 'profile': {'interest_business': 5, 'ability_logic': 5, 'interest_detail': 4, 'interest_tech': 4, 'ability_comm': 3}},
    'Esports': {'key_traits': ['ability_teamwork', 'interest_leading', 'interest_detail'], 'label': 'Gaming Entrepreneur', 'profile': {'ability_teamwork': 5, 'interest_leading': 4, 'interest_detail': 3, 'interest_tech': 5, 'interest_business': 4}},
    'Actuarial Science': {'key_traits': ['ability_logic', 'interest_detail', 'interest_research'], 'label': 'Risk Mathematician', 'profile': {'ability_logic': 5, 'interest_detail': 5, 'interest_research': 5, 'interest_business': 4, 'interest_science': 4}},
    'Applied Mathematics': {'key_traits': ['ability_logic', 'interest_research', 'interest_tech'], 'label': 'Quantitative Modeler', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_tech': 4, 'interest_science': 4, 'interest_detail': 3}},
    'Mathematics with Specializations (Business Application, Data Science)': {'key_traits': ['ability_logic', 'interest_research', 'interest_business'], 'label': 'Applied Logician', 'profile': {'ability_logic': 5, 'interest_research': 4, 'interest_business': 4, 'interest_tech': 4, 'interest_detail': 4}},
    
    # -----------------------------------------------------
    # ENGINEERING, ARCHITECTURE, & DESIGN
    # -----------------------------------------------------
    'Architecture': {'key_traits': ['ability_creativity', 'interest_design', 'ability_spatial'], 'label': 'Creative Space Designer', 'profile': {'ability_creativity': 5, 'interest_design': 5, 'ability_spatial': 5, 'ability_logic': 4, 'interest_building': 4}},
    'Interior Design': {'key_traits': ['ability_creativity', 'interest_design', 'interest_arts'], 'label': 'Indoor Space Stylist', 'profile': {'ability_creativity': 5, 'interest_design': 5, 'interest_arts': 4, 'ability_spatial': 4, 'ability_comm': 3}},
    'Industrial Engineering': {'key_traits': ['interest_business', 'ability_logic', 'ability_teamwork'], 'label': 'Efficiency Optimizer', 'profile': {'interest_business': 5, 'ability_logic': 5, 'ability_teamwork': 4, 'ability_comm': 4, 'ability_practical': 3}},
    'Civil Engineering': {'key_traits': ['ability_practical', 'ability_logic', 'interest_building'], 'label': 'Structural Planner', 'profile': {'ability_practical': 5, 'ability_logic': 5, 'interest_building': 4, 'ability_spatial': 4, 'interest_research': 4}},
    'Computer Engineering': {'key_traits': ['ability_logic', 'interest_tech', 'interest_building'], 'label': 'Hardware Innovator', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'interest_building': 4, 'ability_practical': 4, 'interest_research': 4}},
    'Electrical Engineering': {'key_traits': ['ability_logic', 'interest_tech', 'interest_building'], 'label': 'Power Systems Expert', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'interest_building': 4, 'ability_practical': 4, 'interest_research': 4}},
    'Electronics Engineering': {'key_traits': ['ability_logic', 'interest_tech', 'interest_research'], 'label': 'Circuit Designer', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'interest_research': 4, 'ability_practical': 4, 'interest_building': 3}},
    'Manufacturing & Robotics Engineering': {'key_traits': ['ability_practical', 'interest_building', 'interest_tech'], 'label': 'Robotics Production Lead', 'profile': {'ability_practical': 5, 'interest_building': 5, 'interest_tech': 5, 'ability_logic': 4, 'ability_teamwork': 4}},
    'Metallurgical Engineering': {'key_traits': ['interest_research', 'ability_practical', 'interest_building'], 'label': 'Metal Specialist', 'profile': {'interest_research': 5, 'ability_practical': 5, 'interest_building': 4, 'ability_logic': 4, 'interest_tech': 3}},
    'Construction Engineering & Management': {'key_traits': ['interest_building', 'ability_practical', 'interest_leading'], 'label': 'Project Site Leader', 'profile': {'interest_building': 5, 'ability_practical': 5, 'interest_leading': 4, 'ability_teamwork': 4, 'interest_business': 4}},
    'Geology & Geological Science and Engineering': {'key_traits': ['interest_nature', 'interest_research', 'ability_logic'], 'label': 'Earth Structure Analyst', 'profile': {'interest_nature': 5, 'interest_research': 5, 'ability_logic': 4, 'ability_spatial': 4, 'ability_practical': 3}},
    'Instrumentation & Control Engineering': {'key_traits': ['ability_logic', 'interest_tech', 'ability_practical'], 'label': 'System Automator', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'ability_practical': 4, 'interest_building': 4, 'interest_research': 3}},
    
    # -----------------------------------------------------
    # BUSINESS, MANAGEMENT, & ECONOMICS
    # -----------------------------------------------------
    'Accountancy': {'key_traits': ['ability_logic', 'interest_detail', 'interest_business'], 'label': 'Detail-Oriented Auditor', 'profile': {'ability_logic': 5, 'interest_detail': 5, 'interest_business': 5, 'ability_practical': 3, 'ability_comm': 2}},
    'Internal Auditing': {'key_traits': ['ability_logic', 'interest_detail', 'interest_business'], 'label': 'Compliance Analyst', 'profile': {'ability_logic': 5, 'interest_detail': 5, 'interest_business': 5, 'ability_teamwork': 3, 'ability_comm': 3}},
    'Business Administration': {'key_traits': ['ability_teamwork', 'interest_leading', 'interest_business'], 'label': 'Team Leader', 'profile': {'ability_teamwork': 5, 'interest_leading': 5, 'interest_business': 5, 'ability_comm': 4, 'ability_logic': 3}},
    'Entrepreneurship': {'key_traits': ['interest_leading', 'interest_business', 'ability_creativity'], 'label': 'Innovative Founder', 'profile': {'interest_leading': 5, 'interest_business': 5, 'ability_creativity': 5, 'ability_comm': 4, 'ability_logic': 3}},
    'Financial Management': {'key_traits': ['ability_logic', 'interest_business', 'interest_detail'], 'label': 'Investment Planner', 'profile': {'ability_logic': 5, 'interest_business': 5, 'interest_detail': 4, 'ability_comm': 3, 'interest_leading': 3}},
    'Marketing Management': {'key_traits': ['ability_creativity', 'ability_comm', 'interest_business'], 'label': 'Creative Strategist', 'profile': {'ability_creativity': 5, 'ability_comm': 5, 'interest_business': 4, 'interest_leading': 4, 'interest_design': 3}},
    'Operations Management (Business major)': {'key_traits': ['ability_practical', 'interest_business', 'ability_logic'], 'label': 'Process Optimizer', 'profile': {'ability_practical': 5, 'interest_business': 4, 'ability_logic': 4, 'interest_detail': 4, 'ability_teamwork': 4}},
    'Applied Corporate Management': {'key_traits': ['interest_leading', 'interest_business', 'ability_teamwork'], 'label': 'Corporate Executive', 'profile': {'interest_leading': 5, 'interest_business': 5, 'ability_teamwork': 4, 'ability_comm': 4, 'ability_logic': 3}},
    'Economics': {'key_traits': ['ability_logic', 'interest_research', 'interest_policy'], 'label': 'Policy Analyst', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_policy': 4, 'interest_business': 4, 'ability_comm': 3}},
    'Business Economics': {'key_traits': ['ability_logic', 'interest_business', 'interest_research'], 'label': 'Market Predictor', 'profile': {'ability_logic': 5, 'interest_business': 4, 'interest_research': 4, 'ability_comm': 3, 'interest_leading': 3}},
    'Applied Economics': {'key_traits': ['ability_logic', 'interest_detail', 'interest_business'], 'label': 'Economic Modeler', 'profile': {'ability_logic': 5, 'interest_detail': 5, 'interest_business': 4, 'interest_research': 4, 'interest_policy': 3}},
    'Real Estate': {'key_traits': ['interest_business', 'ability_comm', 'interest_detail'], 'label': 'Property Strategist', 'profile': {'interest_business': 5, 'ability_comm': 5, 'interest_detail': 4, 'interest_leading': 4, 'ability_logic': 3}},
    
    # -----------------------------------------------------
    # HEALTH, LIFE, & NATURAL SCIENCES
    # -----------------------------------------------------
    'Medicine': {'key_traits': ['interest_helping', 'interest_research', 'ability_logic'], 'label': 'Medical Physician', 'profile': {'interest_helping': 5, 'interest_research': 5, 'ability_logic': 5, 'interest_science': 5, 'ability_comm': 4}},
    'Nursing': {'key_traits': ['interest_helping', 'ability_comm', 'ability_teamwork'], 'label': 'Empathetic Caregiver', 'profile': {'interest_helping': 5, 'ability_comm': 5, 'ability_teamwork': 5, 'interest_research': 4, 'ability_practical': 3}},
    'Medical Technology': {'key_traits': ['ability_logic', 'interest_research', 'ability_practical'], 'label': 'Lab Analyst', 'profile': {'ability_logic': 5, 'interest_research': 5, 'ability_practical': 4, 'interest_detail': 4, 'interest_helping': 3}},
    'Pharmaceutical Sciences': {'key_traits': ['ability_logic', 'interest_research', 'interest_detail'], 'label': 'Drug Formulation Expert', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_detail': 4, 'interest_helping': 4, 'ability_practical': 3}},
    'Nutrition & Dietetics': {'key_traits': ['interest_helping', 'interest_research', 'ability_comm'], 'label': 'Wellness Coach', 'profile': {'interest_helping': 5, 'interest_research': 4, 'ability_comm': 5, 'ability_logic': 3, 'ability_practical': 3}},
    'Health Professions': {'key_traits': ['interest_helping', 'interest_research', 'ability_teamwork'], 'label': 'Healthcare Coordinator', 'profile': {'interest_helping': 5, 'interest_research': 4, 'ability_teamwork': 4, 'ability_comm': 4, 'ability_practical': 3}},
    'Clinical Audiology': {'key_traits': ['interest_helping', 'interest_research', 'ability_detail'], 'label': 'Hearing Specialist', 'profile': {'interest_helping': 5, 'interest_research': 4, 'interest_detail': 4, 'ability_logic': 4, 'ability_comm': 4}},
    'Clinical Pharmacy': {'key_traits': ['ability_logic', 'interest_research', 'interest_helping'], 'label': 'Patient Drug Expert', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_helping': 4, 'ability_comm': 4, 'ability_detail': 4}},
    'Human Biology': {'key_traits': ['interest_research', 'interest_science', 'ability_logic'], 'label': 'Human Life Scientist', 'profile': {'interest_research': 5, 'interest_science': 5, 'ability_logic': 5, 'ability_practical': 4, 'interest_helping': 3}},
    'Biology': {'key_traits': ['interest_research', 'ability_logic', 'interest_nature'], 'label': 'Life Scientist', 'profile': {'interest_research': 5, 'ability_logic': 5, 'interest_nature': 4, 'ability_practical': 3, 'interest_helping': 3}},
    'Biochemistry': {'key_traits': ['interest_research', 'ability_logic', 'interest_detail'], 'label': 'Molecular Analyst', 'profile': {'interest_research': 5, 'ability_logic': 5, 'interest_detail': 4, 'interest_science': 5, 'ability_practical': 4}},
    'Biotechnology': {'key_traits': ['interest_research', 'ability_logic', 'interest_tech'], 'label': 'Cellular Innovator', 'profile': {'interest_research': 5, 'ability_logic': 5, 'interest_tech': 4, 'ability_practical': 4, 'ability_teamwork': 3}},
    'Chemistry': {'key_traits': ['interest_research', 'ability_logic', 'ability_practical'], 'label': 'Substance Analyst', 'profile': {'interest_research': 5, 'ability_logic': 5, 'ability_practical': 4, 'interest_tech': 3, 'interest_building': 3}},
    'Physics': {'key_traits': ['ability_logic', 'interest_research', 'interest_tech'], 'label': 'Theoretical Thinker', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_tech': 4, 'interest_building': 3, 'ability_practical': 3}},
    'Applied Physics': {'key_traits': ['ability_logic', 'interest_tech', 'ability_practical'], 'label': 'Practical Engineer', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'ability_practical': 4, 'interest_research': 4, 'interest_building': 3}},
    'Medical Physics': {'key_traits': ['ability_logic', 'interest_research', 'interest_helping'], 'label': 'Medical Device Specialist', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_helping': 4, 'interest_tech': 4, 'ability_practical': 3}},
    'Zoology / Systematics & Ecology': {'key_traits': ['interest_nature', 'interest_research', 'ability_logic'], 'label': 'Animal Classifier', 'profile': {'interest_nature': 5, 'interest_research': 5, 'ability_logic': 4, 'ability_practical': 3, 'interest_helping': 3}},
    'Veterinary or Animal Sciences': {'key_traits': ['interest_nature', 'interest_helping', 'ability_practical'], 'label': 'Animal Care Specialist', 'profile': {'interest_nature': 5, 'interest_helping': 5, 'ability_practical': 4, 'interest_research': 3, 'ability_teamwork': 4}},
    
    # -----------------------------------------------------
    # SOCIAL SCIENCES, HUMANITIES, & LIBERAL ARTS
    # -----------------------------------------------------
    'Psychology': {'key_traits': ['ability_comm', 'interest_helping', 'interest_research'], 'label': 'Insightful Advisor', 'profile': {'ability_comm': 5, 'interest_helping': 5, 'interest_research': 4, 'ability_logic': 3, 'interest_teaching': 3}},
    'Clinical Psychology': {'key_traits': ['interest_helping', 'interest_research', 'ability_comm'], 'label': 'Mental Health Therapist', 'profile': {'interest_helping': 5, 'interest_research': 5, 'ability_comm': 4, 'ability_logic': 4, 'interest_policy': 3}},
    'Political Science': {'key_traits': ['interest_policy', 'ability_comm', 'ability_logic'], 'label': 'Government Analyst', 'profile': {'interest_policy': 5, 'ability_comm': 5, 'ability_logic': 4, 'interest_leading': 4, 'interest_research': 4}},
    'Legal Studies (Law)': {'key_traits': ['ability_logic', 'interest_policy', 'ability_comm'], 'label': 'Rule Interpreter', 'profile': {'ability_logic': 5, 'interest_policy': 5, 'ability_comm': 5, 'interest_detail': 4, 'interest_research': 4}},
    'Public Administration': {'key_traits': ['interest_leading', 'interest_policy', 'ability_comm'], 'label': 'Policy Implementer', 'profile': {'interest_leading': 5, 'interest_policy': 5, 'ability_comm': 4, 'ability_logic': 4, 'interest_business': 3}},
    'International Studies': {'key_traits': ['interest_policy', 'ability_comm', 'interest_arts'], 'label': 'Global Diplomat', 'profile': {'interest_policy': 5, 'ability_comm': 5, 'interest_arts': 4, 'interest_leading': 4, 'interest_research': 3}},
    'Philippine Studies': {'key_traits': ['interest_arts', 'interest_research', 'ability_comm'], 'label': 'Filipino Culture Scholar', 'profile': {'interest_arts': 5, 'interest_research': 4, 'ability_comm': 4, 'interest_policy': 3, 'ability_creativity': 3}},
    'Asian Studies': {'key_traits': ['interest_research', 'interest_arts', 'ability_comm'], 'label': 'Regional Expert', 'profile': {'interest_research': 5, 'interest_arts': 4, 'ability_comm': 4, 'interest_policy': 3, 'interest_teaching': 3}},
    'Linguistics': {'key_traits': ['ability_logic', 'interest_research', 'ability_comm'], 'label': 'Language Scientist', 'profile': {'ability_logic': 5, 'interest_research': 4, 'ability_comm': 4, 'interest_arts': 3, 'interest_tech': 3}},
    'Social Sciences': {'key_traits': ['interest_helping', 'interest_research', 'ability_logic'], 'label': 'Human Behavior Analyst', 'profile': {'interest_helping': 5, 'interest_research': 4, 'ability_logic': 4, 'ability_comm': 4, 'interest_policy': 3}},
    'Archaeology / Archaeological Studies': {'key_traits': ['interest_research', 'interest_nature', 'ability_detail'], 'label': 'Historical Detective', 'profile': {'interest_research': 5, 'interest_nature': 5, 'interest_detail': 4, 'ability_logic': 3, 'ability_practical': 3}},

    # -----------------------------------------------------
    # COMMUNICATION, MEDIA, & CREATIVE ARTS
    # -----------------------------------------------------
    'Broadcasting': {'key_traits': ['ability_comm', 'ability_creativity', 'interest_tech'], 'label': 'Media Producer', 'profile': {'ability_comm': 5, 'ability_creativity': 5, 'interest_tech': 4, 'interest_arts': 4, 'interest_leading': 3}},
    'Journalism': {'key_traits': ['ability_comm', 'interest_policy', 'interest_research'], 'label': 'Investigative Reporter', 'profile': {'ability_comm': 5, 'interest_policy': 4, 'interest_research': 4, 'interest_arts': 3, 'ability_logic': 3}},
    'Advertising': {'key_traits': ['ability_creativity', 'interest_design', 'interest_business'], 'label': 'Persuasion Strategist', 'profile': {'ability_creativity': 5, 'interest_design': 5, 'interest_business': 4, 'ability_comm': 4, 'interest_leading': 3}},
    'Digital Film & Media Production': {'key_traits': ['ability_creativity', 'interest_design', 'interest_tech'], 'label': 'Visual Storyteller', 'profile': {'ability_creativity': 5, 'interest_design': 5, 'interest_tech': 4, 'interest_arts': 4, 'ability_teamwork': 3}},
    'Multimedia Arts': {'key_traits': ['ability_creativity', 'interest_design', 'interest_arts'], 'label': 'Creative Visualizer', 'profile': {'ability_creativity': 5, 'interest_design': 5, 'interest_arts': 4, 'interest_tech': 4, 'ability_practical': 3}},
    'Arts': {'key_traits': ['ability_creativity', 'interest_arts', 'interest_design'], 'label': 'Creative Master', 'profile': {'ability_creativity': 5, 'interest_arts': 5, 'interest_design': 5, 'interest_teaching': 3, 'ability_logic': 2}},
    'Theatre & Performance': {'key_traits': ['ability_creativity', 'ability_comm', 'interest_arts'], 'label': 'Performance Artist', 'profile': {'ability_creativity': 5, 'ability_comm': 5, 'interest_arts': 5, 'interest_teaching': 4, 'ability_teamwork': 4}},
    'Creative Writing': {'key_traits': ['ability_creativity', 'interest_arts', 'ability_comm'], 'label': 'Literary Visionary', 'profile': {'ability_creativity': 5, 'interest_arts': 5, 'ability_comm': 4, 'interest_research': 4, 'ability_logic': 3}},
    'Mass Communication & Organizational Communication': {'key_traits': ['ability_comm', 'interest_leading', 'interest_business'], 'label': 'Corporate Communicator', 'profile': {'ability_comm': 5, 'interest_leading': 4, 'interest_business': 4, 'ability_teamwork': 4, 'ability_creativity': 3}},
    'Voice & Vocal Performance': {'key_traits': ['interest_arts', 'ability_creativity', 'ability_comm'], 'label': 'Vocal Performer', 'profile': {'interest_arts': 5, 'ability_creativity': 5, 'ability_comm': 4, 'interest_teaching': 3, 'ability_practical': 3}},
    
    # -----------------------------------------------------
    # EDUCATION & LIBRARY SCIENCE
    # -----------------------------------------------------
    'Education': {'key_traits': ['interest_teaching', 'ability_comm', 'interest_helping'], 'label': 'Inspirational Mentor', 'profile': {'interest_teaching': 5, 'ability_comm': 5, 'interest_helping': 4, 'ability_teamwork': 4, 'ability_creativity': 3}},
    'Art Education': {'key_traits': ['interest_arts', 'interest_teaching', 'ability_creativity'], 'label': 'Creative Instructor', 'profile': {'interest_arts': 5, 'interest_teaching': 5, 'ability_creativity': 5, 'ability_comm': 4, 'ability_teamwork': 3}},
    'Educational Psychology': {'key_traits': ['interest_teaching', 'interest_research', 'interest_helping'], 'label': 'Learning Behavior Specialist', 'profile': {'interest_teaching': 5, 'interest_research': 4, 'interest_helping': 4, 'ability_logic': 4, 'ability_comm': 4}},
    
    # -----------------------------------------------------
    # APPLIED, TECHNICAL, & VOCATIONAL SCIENCES
    # -----------------------------------------------------
    'Forensic': {'key_traits': ['ability_logic', 'interest_research', 'ability_practical'], 'label': 'Crime Scene Analyst', 'profile': {'ability_logic': 5, 'interest_research': 5, 'ability_practical': 4, 'interest_policy': 4, 'interest_detail': 4}},
    'Criminology': {'key_traits': ['ability_logic', 'interest_policy', 'interest_leading'], 'label': 'Justice Investigator', 'profile': {'ability_logic': 5, 'interest_policy': 5, 'interest_leading': 4, 'ability_comm': 4, 'ability_practical': 3}},
    'Geology & Geological Science and Engineering': {'key_traits': ['interest_nature', 'interest_research', 'ability_logic'], 'label': 'Earth Structure Analyst', 'profile': {'interest_nature': 5, 'interest_research': 5, 'ability_logic': 4, 'ability_spatial': 4, 'ability_practical': 3}},
    'Vehicle/Automotive Engineering Technology': {'key_traits': ['ability_practical', 'interest_building', 'interest_tech'], 'label': 'Hands-on Technician', 'profile': {'ability_practical': 5, 'interest_building': 5, 'interest_tech': 4, 'ability_logic': 3, 'ability_teamwork': 3}},
    'Apparel and Fashion Technology': {'key_traits': ['ability_practical', 'interest_design', 'interest_arts'], 'label': 'Garment Engineer', 'profile': {'ability_practical': 5, 'interest_design': 5, 'interest_arts': 4, 'ability_creativity': 4, 'interest_business': 3}},
    'Industrial Arts': {'key_traits': ['ability_practical', 'interest_building', 'interest_tech'], 'label': 'Skilled Craftsman', 'profile': {'ability_practical': 5, 'interest_building': 5, 'interest_tech': 4, 'ability_logic': 3, 'ability_teamwork': 3}},
    'Applied Science — Laboratory Technology (BAS-LT)': {'key_traits': ['interest_research', 'ability_practical', 'interest_detail'], 'label': 'Lab Technician', 'profile': {'interest_research': 5, 'ability_practical': 5, 'interest_detail': 4, 'ability_logic': 4, 'interest_science': 4}},
    
    # -----------------------------------------------------
    # PUBLIC SERVICE & HOSPITALITY
    # -----------------------------------------------------
    'Community Development': {'key_traits': ['interest_helping', 'ability_teamwork', 'interest_policy'], 'label': 'Grassroots Organizer', 'profile': {'interest_helping': 5, 'ability_teamwork': 5, 'interest_policy': 4, 'ability_comm': 4, 'interest_teaching': 3}},
    'Public Administration': {'key_traits': ['interest_leading', 'interest_policy', 'ability_comm'], 'label': 'Policy Implementer', 'profile': {'interest_leading': 5, 'interest_policy': 5, 'ability_comm': 4, 'ability_logic': 4, 'interest_business': 3}},
    'Tourism Management': {'key_traits': ['ability_comm', 'interest_helping', 'interest_leading'], 'label': 'Travel Planner', 'profile': {'ability_comm': 5, 'interest_helping': 4, 'interest_leading': 4, 'interest_arts': 4, 'interest_business': 3}},
    'Hotel, Restaurant & Institutional Management': {'key_traits': ['interest_helping', 'interest_business', 'ability_practical'], 'label': 'Service Operations Leader', 'profile': {'interest_helping': 5, 'interest_business': 4, 'ability_practical': 4, 'interest_leading': 4, 'ability_teamwork': 5}},
    'Cruise Line Operations': {'key_traits': ['interest_helping', 'ability_teamwork', 'ability_practical'], 'label': 'Maritime Service Specialist', 'profile': {'interest_helping': 5, 'ability_teamwork': 5, 'ability_practical': 4, 'ability_comm': 4, 'interest_leading': 3}},
    'Transportation Engineering': {'key_traits': ['ability_logic', 'interest_building', 'ability_practical'], 'label': 'Traffic Flow Designer', 'profile': {'ability_logic': 5, 'interest_building': 5, 'ability_practical': 4, 'interest_tech': 3, 'interest_research': 3}},
    'Real Estate': {'key_traits': ['interest_business', 'ability_comm', 'interest_detail'], 'label': 'Property Strategist', 'profile': {'interest_business': 5, 'ability_comm': 5, 'interest_detail': 4, 'interest_leading': 4, 'ability_logic': 3}},
    'Marine / Maritime-related': {'key_traits': ['interest_nature', 'interest_building', 'ability_practical'], 'label': 'Seafaring Professional', 'profile': {'interest_nature': 5, 'interest_building': 4, 'ability_practical': 4, 'ability_teamwork': 4, 'interest_tech': 3}},
    
    # -----------------------------------------------------
    # OTHER SPECIALIZED COURSES
    # -----------------------------------------------------
    'Clinical Audiology': {'key_traits': ['interest_helping', 'interest_research', 'ability_detail'], 'label': 'Hearing Specialist', 'profile': {'interest_helping': 5, 'interest_research': 4, 'interest_detail': 4, 'ability_logic': 4, 'ability_comm': 4}},
    'Clinical Pharmacy': {'key_traits': ['ability_logic', 'interest_research', 'interest_helping'], 'label': 'Patient Drug Expert', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_helping': 4, 'ability_comm': 4, 'interest_detail': 4}},
    'Clinical Psychology': {'key_traits': ['interest_helping', 'interest_research', 'ability_comm'], 'label': 'Mental Health Therapist', 'profile': {'interest_helping': 5, 'interest_research': 5, 'ability_comm': 4, 'ability_logic': 4, 'interest_policy': 3}},
    'Culinary Arts': {'key_traits': ['ability_practical', 'ability_creativity', 'interest_business'], 'label': 'Creative Chef', 'profile': {'ability_practical': 5, 'ability_creativity': 5, 'interest_business': 4, 'interest_detail': 4, 'ability_teamwork': 4}},
    'Dentistry': {'key_traits': ['interest_helping', 'ability_practical', 'interest_science'], 'label': 'Oral Health Expert', 'profile': {'interest_helping': 5, 'ability_practical': 5, 'interest_science': 4, 'interest_detail': 4, 'ability_logic': 4}},
    'Forensic': {'key_traits': ['ability_logic', 'interest_research', 'ability_practical'], 'label': 'Crime Scene Analyst', 'profile': {'ability_logic': 5, 'interest_research': 5, 'ability_practical': 4, 'interest_policy': 4, 'interest_detail': 4}},
    'Health Professions': {'key_traits': ['interest_helping', 'interest_research', 'ability_teamwork'], 'label': 'Healthcare Coordinator', 'profile': {'interest_helping': 5, 'interest_research': 4, 'ability_teamwork': 4, 'ability_comm': 4, 'ability_practical': 3}},
    'Human Biology': {'key_traits': ['interest_research', 'interest_science', 'ability_logic'], 'label': 'Human Life Scientist', 'profile': {'interest_research': 5, 'interest_science': 5, 'ability_logic': 5, 'ability_practical': 4, 'interest_helping': 3}},
    'Human Kinetics': {'key_traits': ['ability_practical', 'interest_sports', 'interest_teaching'], 'label': 'Movement Specialist', 'profile': {'ability_practical': 5, 'interest_sports': 5, 'interest_teaching': 4, 'interest_helping': 4, 'ability_comm': 3}},
    'Legal Studies (Law)': {'key_traits': ['ability_logic', 'interest_policy', 'ability_comm'], 'label': 'Rule Interpreter', 'profile': {'ability_logic': 5, 'interest_policy': 5, 'ability_comm': 5, 'interest_detail': 4, 'interest_research': 4}},
    'Medical Physics': {'key_traits': ['ability_logic', 'interest_research', 'interest_helping'], 'label': 'Medical Device Specialist', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_helping': 4, 'interest_tech': 4, 'ability_practical': 3}},
    'Medicine': {'key_traits': ['interest_helping', 'interest_research', 'ability_logic'], 'label': 'Medical Physician', 'profile': {'interest_helping': 5, 'interest_research': 5, 'ability_logic': 5, 'interest_science': 5, 'ability_comm': 4}},
    'Nursing': {'key_traits': ['interest_helping', 'ability_comm', 'ability_teamwork'], 'label': 'Empathetic Caregiver', 'profile': {'interest_helping': 5, 'ability_comm': 5, 'ability_teamwork': 5, 'interest_research': 4, 'ability_practical': 3}},
    'Nutrition & Dietetics': {'key_traits': ['interest_helping', 'interest_research', 'ability_comm'], 'label': 'Wellness Coach', 'profile': {'interest_helping': 5, 'interest_research': 4, 'ability_comm': 5, 'ability_logic': 3, 'ability_practical': 3}},
    'Organizational Communication': {'key_traits': ['ability_comm', 'interest_leading', 'interest_business'], 'label': 'Corporate Communicator', 'profile': {'ability_comm': 5, 'interest_leading': 4, 'interest_business': 4, 'ability_teamwork': 4, 'ability_creativity': 3}},
    'Pharmaceutical Sciences': {'key_traits': ['ability_logic', 'interest_research', 'interest_detail'], 'label': 'Drug Formulation Expert', 'profile': {'ability_logic': 5, 'interest_research': 5, 'interest_detail': 4, 'interest_helping': 4, 'ability_practical': 3}},
    'Real Estate': {'key_traits': ['interest_business', 'ability_comm', 'interest_detail'], 'label': 'Property Strategist', 'profile': {'interest_business': 5, 'ability_comm': 5, 'interest_detail': 4, 'interest_leading': 4, 'ability_logic': 3}},
    'Religious & Values Education': {'key_traits': ['interest_teaching', 'interest_helping', 'ability_comm'], 'label': 'Spiritual Guide', 'profile': {'interest_teaching': 5, 'interest_helping': 5, 'ability_comm': 4, 'ability_creativity': 3, 'ability_teamwork': 3}},
    'Theatre & Performance': {'key_traits': ['ability_creativity', 'ability_comm', 'interest_arts'], 'label': 'Performance Artist', 'profile': {'ability_creativity': 5, 'ability_comm': 5, 'interest_arts': 5, 'interest_teaching': 4, 'ability_teamwork': 4}},
    'Veterinary or Animal Sciences': {'key_traits': ['interest_nature', 'interest_helping', 'ability_practical'], 'label': 'Animal Care Specialist', 'profile': {'interest_nature': 5, 'interest_helping': 5, 'ability_practical': 4, 'interest_research': 3, 'ability_teamwork': 4}},
    'Zoology / Systematics & Ecology': {'key_traits': ['interest_nature', 'interest_research', 'ability_logic'], 'label': 'Animal Classifier', 'profile': {'interest_nature': 5, 'interest_research': 5, 'ability_logic': 4, 'ability_practical': 3, 'interest_helping': 3}},
}
def get_recommendations_from_assessment(assessment):

    all_courses = Course.objects.all().prefetch_related('offering_universities')

    user_ratings = {
        'interest_research': assessment.interest_research, 'interest_arts': assessment.interest_arts,
        'interest_policy': assessment.interest_policy, 'interest_design': assessment.interest_design,
        'interest_tech': assessment.interest_tech, 'interest_building': assessment.interest_building,
        'interest_nature': assessment.interest_nature, 'ability_spatial': assessment.ability_spatial,
        'interest_detail': assessment.interest_detail, 'interest_leading': assessment.interest_leading,
        'interest_helping': assessment.interest_helping, 'ability_teamwork': assessment.ability_teamwork,
        'ability_logic': assessment.ability_logic, 'ability_creativity': assessment.ability_creativity,
        'ability_comm': assessment.ability_comm, 'ability_practical': assessment.ability_practical,
        'interest_science': assessment.interest_science, 'interest_teaching': assessment.interest_teaching, 
        'interest_business': assessment.interest_business, 'interest_sports': assessment.interest_sports,
    }

    course_scores = {}
    for course_obj in all_courses:
        course_name = course_obj.name
        persona = COURSE_PERSONAS.get(course_name)
        
        if not persona: continue

        key_traits = persona.get('key_traits', [])
        match_score = 0
        for trait, ideal_score in persona.get('profile', {}).items():
            user_score = user_ratings.get(trait, 0)
            score_increment = 5 - abs(user_score - ideal_score)
            weight = 3 if trait in key_traits else 1
            match_score += score_increment * weight
            
        course_scores[course_name] = {'score': match_score, 'object': course_obj}

    top_courses_names = [assessment.recommended_course_1, assessment.recommended_course_2, assessment.recommended_course_3]
    top_courses_data = []

    # Get the raw scores for scaling (requires finding the original top scores)
    ranked_courses_data = sorted(course_scores.items(), key=lambda item: item[1]['score'], reverse=True)
    top_score = ranked_courses_data[0][1]['score'] if ranked_courses_data else 0

    base_score = 80
    for i, course_name in enumerate(top_courses_names):
        if not course_name: continue
        
        data = course_scores.get(course_name)
        if not data: continue
        
        course_obj = data['object']
        
        score_difference = (top_score - data['score']) if top_score > 0 else 0
        scaled_percentage = max(base_score, 98 - (i * 5) - (score_difference // 5))

        insights = get_in_depth_insights(course_name, user_ratings)
        uni_list = []
        for uni in course_obj.offering_universities.all():
            clean_name = uni.name.replace('(', '').replace(')', '').strip()
            uni_slug = clean_name.replace(' ', '-').lower()
            uni_list.append({'name': uni.name, 'slug': uni_slug})
        
        top_courses_data.append({
            'course': course_name, 
            'match_score': f"{scaled_percentage}%", 
            'insights': insights,
            'universities': uni_list
        })

    return top_courses_data

def email_recommendations_view(request, assessment_id):
    if request.method == 'POST':
        recipient_email = request.POST.get('recipient_email')
        
        if not recipient_email:
            messages.error(request, "Please provide a valid email address.")
            return redirect('recommendation_result_with_id', assessment_id=assessment_id)

        try:
            assessment = get_object_or_404(Assessment, id=assessment_id)
            
            # 1. Regenerate the data needed for the email (top 3 courses, insights, etc.)
            recommendations = get_recommendations_from_assessment(assessment)

            # 2. Render the email template
            email_context = {
                'recommendations': recommendations,
                'student_name': assessment.name or 'Valued User',
                'timestamp': assessment.timestamp.strftime("%B %d, %Y"),
                'is_email_view': True # Flag to adjust rendering for email
            }
            html_message = render_to_string('recommender/email/recommendation_email.html', email_context)
            
            # 3. Send the email
            subject = 'Your AlignEd Course Recommendation Results'
            
            email = EmailMessage(
                subject,
                html_message,
                settings.EMAIL_HOST_USER,
                [recipient_email]
            )
            email.content_subtype = "html" # Main content is now HTML
            email.send()

            messages.success(request, f"Your results have been sent to {recipient_email}!")
            return redirect('recommendation_result_with_id', assessment_id=assessment_id)

        except Assessment.DoesNotExist:
            messages.error(request, "Assessment record not found.")
            return redirect('assessment')
        except Exception as e:
            messages.error(request, f"Failed to send email. Error: {e}")
            return redirect('recommendation_result_with_id', assessment_id=assessment_id)
            
    # If not POST, just redirect back to the results page
    return redirect('recommendation_result_with_id', assessment_id=assessment_id)

def get_in_depth_insights(course_name, user_ratings):
    persona = COURSE_PERSONAS.get(course_name)
    if not persona:
        return {"strengths": [f"This course is a great fit for your overall profile in your chosen field."], "growth": [], "chart_data": None}

    skill_map = {'ability_logic': 'Logical Thinking', 'ability_creativity': 'Creativity', 'ability_comm': 'Communication', 'ability_practical': 'Practical Skills', 'ability_teamwork': 'Teamwork', 'ability_spatial': 'Spatial Reasoning'}
    interest_map = {'interest_tech': 'Technology', 'interest_research': 'Research/Science', 'interest_business': 'Business', 'interest_leading': 'Leading', 'interest_helping': 'Helping Others', 'interest_design': 'Design', 'interest_building': 'Building Things', 'interest_arts': 'Arts', 'interest_teaching': 'Teaching', 'interest_nature': 'Nature', 'interest_policy': 'Social Policy', 'interest_detail': 'Detail Orientation'}

    strengths, growth_areas, chart_labels, user_scores, ideal_scores = [], [], [], [], []
    key_traits = persona.get('key_traits', [])

    chart_traits = list(set(key_traits + list(persona.get('profile', {}).keys())[:5]))

    for trait in chart_traits:
        user_score = user_ratings.get(trait, 0)
        ideal_score = persona.get('profile', {}).get(trait, 3)
        trait_name = skill_map.get(trait) or interest_map.get(trait) or trait.replace('_', ' ').title()

        if trait_name:
            chart_labels.append(trait_name)
            user_scores.append(user_score)
            ideal_scores.append(ideal_score)

            if trait in key_traits:
                if user_score >= ideal_score or user_score >= 4:
                    strengths.append(f"Your high score in <strong>{trait_name}</strong> is a great asset for this field.")
                elif user_score < ideal_score - 1:
                    growth_areas.append(f"Developing your <strong>{trait_name}</strong> skills could further boost your success.")

    chart_data = {"labels": chart_labels, "user_scores": user_scores, "ideal_scores": ideal_scores}
    if not strengths and not growth_areas:
        strengths.append("This course aligns with a good balance of your skills and interests.")

    return {"strengths": strengths, "growth": growth_areas, "chart_data": json.dumps(chart_data)}


def is_superuser(user):
    return user.is_authenticated and user.is_superuser

def dashboard_view(request):
    import json
    from django.db.models import Count
    total_assessments = Assessment.objects.count()
    available_courses = Course.objects.count()
    feedback_assessments = Assessment.objects.filter(feedback_submitted=True)
    total_feedback = feedback_assessments.count()
    high_feedback_count = feedback_assessments.filter(feedback_rating_1__gte=4).count()
    
    agreement_score = (high_feedback_count / total_feedback * 100) if total_feedback > 0 else 0
    
    assessments_by_strand = Assessment.objects.values('shs_strand').annotate(count=Count('shs_strand')).order_by('-count')
    strand_data_for_js = json.dumps(list(assessments_by_strand))
    
    top_courses_query = Assessment.objects.values('recommended_course_1').annotate(count=Count('recommended_course_1')).exclude(recommended_course_1__exact='').order_by('-count')[:3]
    
    top_courses_with_icons = []
    for item in top_courses_query:
        course_name = item['recommended_course_1']
        course_obj = Course.objects.filter(name=course_name).first()
        top_courses_with_icons.append({
            'name': course_name, 
            'count': item['count'], 
            'icon': course_obj.icon if course_obj else 'book'
        })
        
    top_courses_json = json.dumps(top_courses_with_icons)
    
    context = {
        'active_page': 'dashboard', 
        'total_assessments_count': total_assessments, 
        'available_courses_count': available_courses, 
        'feedback_agreement_score': agreement_score, 
        
        'top_recommended_courses_json': top_courses_json,
        'strand_data_json': strand_data_for_js 
    }
    return render(request, 'recommender/dashboard.html', context)

def courses_view(request):
    all_courses = Course.objects.all().order_by('name')
    context = {'active_page': 'courses', 'courses': all_courses}
    return render(request, 'recommender/courses.html', context)

def about_view(request):
    context = {'active_page': 'about'}
    return render(request, 'recommender/about.html', context)

def assessment_view(request):
    # Step 2
    step2_items = [
        {"name": "interest_research", "label": "Conducting detailed research and experiments", "icon": "search"}, 
        {"name": "interest_arts", "label": "Arts, writing, or creative expression", "icon": "edit-3"},
        {"name": "interest_policy", "label": "Public affairs, law, or social justice issues", "icon": "flag"}, 
        {"name": "interest_design", "label": "Graphic design, digital arts, or aesthetics", "icon": "pen-tool"}
    ]

    # Step 3 
    step3_items = [
        {"name": "interest_tech", "label": "Technology, coding, or software", "icon": "code"},
        {"name": "interest_building", "label": "Building or tinkering with physical things", "icon": "tool"},
        {"name": "interest_nature", "label": "Working with plants, animals, or environment", "icon": "feather"},
        {"name": "ability_spatial", "label": "Visualizing 3D objects and spaces (blueprints)", "icon": "maximize"}
    ]

    # Step 4 
    step4_items = [
        {"name": "interest_detail", "label": "Handling detailed administrative or financial tasks", "icon": "file-text"}, 
        {"name": "interest_leading", "label": "Organizing events or leading teams", "icon": "users"},
        {"name": "interest_helping", "label": "Advising, counseling, or helping people", "icon": "heart"},
        {"name": "ability_teamwork", "label": "Working closely and collaborating in a team", "icon": "users"}
    ]

    # Step 5
    step5_items = [
        {"name": "ability_logic", "label": "Logical thinking and problem solving", "icon": "cpu"},
        {"name": "ability_creativity", "label": "Creativity & original ideas", "icon": "feather"},
        {"name": "ability_comm", "label": "Verbal and written communication", "icon": "message-circle"},
        {"name": "ability_practical", "label": "Practical, hands-on skills", "icon": "tool"}
    ]
    context = {'active_page': 'assessment','step2_items': step2_items,'step3_items': step3_items,'step4_items': step4_items,'step5_items': step5_items}
    return render(request, 'recommender/assessment.html', context)

def university_info_view(request, uni_slug):
    
    name_parts = uni_slug.replace('-', ' ').title().split()
    
    try:
        search_name = ' '.join(name_parts)
        
        from django.db.models import Q
        
        university = University.objects.filter(
            Q(name__iexact=search_name) |
            Q(name__icontains=name_parts[0]) 
        ).first()

        if not university:
            raise Http404("University information not found.")
        
    except University.DoesNotExist:
        raise Http404("University information not found.")
        
    context = {
        'university': university,
        'active_page': 'university_info',
    }
    return render(request, 'recommender/university_info.html', context)

def recommendation_view(request, assessment_id=None):
    # Check if models were loaded globally; if not, return a server error
    if FIELD_MODEL is None or ENCODERS is None:
        # Return a 500 status with an explanation
        return HttpResponseServerError("The recommendation system is offline: ML models failed to load at startup.")

    if request.method == 'POST':
        try:
            # Use the pre-loaded global models/encoders
            field_model = FIELD_MODEL
            encoders = ENCODERS

            form_data = request.POST
            
            # --- Assessment Creation ---
            new_assessment = Assessment.objects.create(
                name=form_data.get('name'), school=form_data.get('school'),
                shs_strand=form_data.get('shs_strand'), tvl_strand=form_data.get('tvl_strand'),
                interest_research=int(form_data.get('interest_research', 0)), interest_arts=int(form_data.get('interest_arts', 0)),
                interest_policy=int(form_data.get('interest_policy', 0)), interest_design=int(form_data.get('interest_design', 0)),
                interest_tech=int(form_data.get('interest_tech', 0)), interest_building=int(form_data.get('interest_building', 0)), 
                interest_nature=int(form_data.get('interest_nature', 0)), ability_spatial=int(form_data.get('ability_spatial', 0)),
                interest_detail=int(form_data.get('interest_detail', 0)), interest_leading=int(form_data.get('interest_leading', 0)), 
                interest_helping=int(form_data.get('interest_helping', 0)), ability_teamwork=int(form_data.get('ability_teamwork', 0)),
                ability_logic=int(form_data.get('ability_logic', 0)), ability_creativity=int(form_data.get('ability_creativity', 0)),
                ability_comm=int(form_data.get('ability_comm', 0)), ability_practical=int(form_data.get('ability_practical', 0)),
            )
            
            # --- Prediction Logic ---
            data_for_prediction = {feature: form_data.get(feature, 0) for feature in field_model.feature_names_in_}
            if 'tvl_strand' not in form_data or not data_for_prediction.get('tvl_strand'): data_for_prediction['tvl_strand'] = 'none'

            df_user = pd.DataFrame([data_for_prediction])
            for column, encoder in encoders.items():
                if column in df_user.columns:
                    value_to_transform = [df_user.iloc[0][column]]
                    try: 
                        encoded_value = encoder.transform(value_to_transform)[0]
                        df_user.at[0, column] = encoded_value
                    except ValueError: 
                        df_user.at[0, column] = 0
            df_user = df_user[list(field_model.feature_names_in_)].apply(pd.to_numeric)
            
            field_probabilities = field_model.predict_proba(df_user)[0]
            top_3_field_indices = field_probabilities.argsort()[-3:][::-1]
            top_3_field_codes = field_model.classes_[top_3_field_indices]
            
            # --- Scoring Logic ---
            user_ratings = {k: int(v) for k, v in form_data.items() if k.startswith(('interest_', 'ability_'))}
            all_qualifying_courses = Course.objects.filter(field_category__in=top_3_field_codes).prefetch_related('offering_universities')
            course_scores = {}
            
            for course_obj in all_qualifying_courses:
                course_name = course_obj.name
                persona = COURSE_PERSONAS.get(course_name)
                
                if not persona: continue 

                key_traits = persona.get('key_traits', [])
                match_score = 0
                for trait, ideal_score in persona.get('profile', {}).items():
                    user_score = user_ratings.get(trait, 0)
                    score_increment = 5 - abs(user_score - ideal_score) 
                    weight = 3 if trait in key_traits else 1
                    match_score += score_increment * weight 
                
                course_scores[course_name] = {'score': match_score, 'object': course_obj}

            ranked_courses_data = sorted(course_scores.items(), key=lambda item: item[1]['score'], reverse=True)
            top_3_ranked_courses = ranked_courses_data[:3]

            # --- Formatting Recommendations ---
            recommendations = []
            base_score = 80
            for i, (course, data) in enumerate(top_3_ranked_courses):
                course_obj = data['object']
                
                offering_universities = course_obj.offering_universities.all()
                uni_list = []
                for uni in offering_universities:
                    clean_name = uni.name.replace('(', '').replace(')', '').strip()
                    uni_slug = clean_name.replace(' ', '-').lower()
                    uni_list.append({'name': uni.name, 'slug': uni_slug})
                
                score_difference = (top_3_ranked_courses[0][1]['score'] - data['score']) if top_3_ranked_courses else 0
                scaled_percentage = max(base_score, 98 - (i * 5) - (score_difference // 5))
                
                insights = get_in_depth_insights(course, user_ratings)
                
                recommendations.append({
                    'course': course, 
                    'match_score': f"{scaled_percentage}%", 
                    'insights': insights,
                    'universities': uni_list
                })
            
            # --- Save Recommendation Results ---
            new_assessment.recommended_course_1 = recommendations[0]['course'] if recommendations else ''
            new_assessment.recommended_course_2 = recommendations[1]['course'] if len(recommendations) > 1 else ''
            new_assessment.recommended_course_3 = recommendations[2]['course'] if len(recommendations) > 2 else ''
            new_assessment.save()
            
            return redirect('recommendation_result_with_id', assessment_id=new_assessment.id)
            
        except Exception as e:
            # Catch errors during prediction, scoring, or saving
            error_msg = f"Recommendation System Error: {e}. Check AI models and database setup."
            return render(request, 'recommender/error.html', {'error_message': error_msg})
    
    # --- GET Request Handling (Loading results by ID) ---
    if assessment_id is not None:
        try:
            assessment = get_object_or_404(Assessment, id=assessment_id)
            
            recommendations = get_recommendations_from_assessment(assessment)
            
            context = {'recommendations': recommendations, 'assessment_id': assessment.id}
            return render(request, 'recommender/recommendation_result.html', context)
        
        except Http404:
            messages.error(request, "Assessment ID not found.")
            return redirect('assessment')
        except Exception as e:
            error_msg = f"Error loading results: {e}"
            return render(request, 'recommender/error.html', {'error_message': error_message})
            
    # Default case: user accessed /recommendation/ directly via GET without ID
    return redirect('assessment')

def submit_feedback_view(request, assessment_id):
    if request.method == 'POST':
        try:
            assessment = get_object_or_404(Assessment, id=assessment_id)
            data = json.loads(request.body)
            rec_number, rating = data.get('recommendation_number'), data.get('rating')
            if rec_number not in [1, 2, 3] or not isinstance(rating, int): return JsonResponse({'status': 'error', 'message': 'Invalid data.'}, status=400)
            setattr(assessment, f'feedback_rating_{rec_number}', rating)
            assessment.feedback_submitted = True
            assessment.save()
            return JsonResponse({'status': 'success', 'message': 'Feedback saved.'})
        except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

def generate_feedback_data_view(request):
    import pandas as pd 
    assessments_with_feedback = Assessment.objects.filter(feedback_submitted=True)
    new_training_data = []
    
    
    course_field_map = {c.name: c.field_category for c in Course.objects.all()}

    for assessment in assessments_with_feedback:
        base_data = {'shs_strand': assessment.shs_strand, 'tvl_strand': assessment.tvl_strand, 'interest_science': assessment.interest_science, 'interest_arts': assessment.interest_arts, 'interest_teaching': assessment.interest_teaching, 'interest_business': assessment.interest_business, 'interest_tech': assessment.interest_tech, 'interest_design': assessment.interest_design, 'interest_sports': assessment.interest_sports, 'interest_building': assessment.interest_building, 'interest_nature': assessment.interest_nature, 'interest_leading': assessment.interest_leading, 'interest_helping': assessment.interest_helping, 'ability_logic': assessment.ability_logic, 'ability_creativity': assessment.ability_creativity, 'ability_comm': assessment.ability_comm, 'ability_practical': assessment.ability_practical, 'ability_teamwork': assessment.ability_teamwork}
        
        def append_feedback(course_name, rating):
            if course_name:
                new_row = base_data.copy()
                new_row['course'] = course_name
                new_row['field_category'] = course_field_map.get(course_name, 'GAS') 
                new_training_data.append(new_row)

        if assessment.feedback_rating_1 and assessment.feedback_rating_1 >= 4:
            append_feedback(assessment.recommended_course_1, assessment.feedback_rating_1)
        if assessment.feedback_rating_2 and assessment.feedback_rating_2 >= 4:
            append_feedback(assessment.recommended_course_2, assessment.feedback_rating_2)
        if assessment.feedback_rating_3 and assessment.feedback_rating_3 >= 4:
            append_feedback(assessment.recommended_course_3, assessment.feedback_rating_3)
            
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="feedback_generated_dataset.csv"'
    
    if not new_training_data:
        writer = csv.writer(response)
        writer.writerow(['No new high-rated feedback to generate data from.'])
        return response
        
    df = pd.DataFrame(new_training_data)
    df.to_csv(path_or_buf=response, index=False)
    return response

def admin_password_reset_request_view(request):
    from django.contrib.auth.forms import PasswordResetForm
    from django.contrib.auth.tokens import default_token_generator
    
    if request.method == "POST":
        admin_user = User.objects.filter(is_superuser=True).order_by('pk').first()
        if admin_user and admin_user.email:
            form = PasswordResetForm({'email': admin_user.email})
            if form.is_valid():
                opts = {"use_https": request.is_secure(), "token_generator": default_token_generator, "from_email": settings.EMAIL_HOST_USER, "email_template_name": "recommender/registration/password_reset_email.html", "subject_template_name": "recommender/registration/password_reset_subject.txt", "request": request}
                form.save(**opts)
                return redirect('password_reset_done')
            else: messages.error(request, "Could not process the password reset for the admin account.")
        else: messages.error(request, "Admin account not found or has no email address configured.")
        return redirect('login') 
    return render(request, 'recommender/registration/password_reset_form.html')

def login_view(request):
    if request.user.is_authenticated: return redirect('admin_dashboard')
    if request.method == 'POST' and '2fa_code' in request.POST:
        user_id = request.session.get('2fa_user_id')
        if not user_id: messages.error(request, 'Your session has expired.'); return redirect('login')
        expiry_time_str = request.session.get('2fa_expiry')
        if datetime.now().isoformat() > expiry_time_str:
            messages.error(request, 'The verification code has expired.')
            del request.session['2fa_user_id'], request.session['2fa_code'], request.session['2fa_expiry']
            return redirect('login')
        if request.POST.get('2fa_code') == request.session.get('2fa_code'):
            try: user = User.objects.get(pk=user_id)
            except User.DoesNotExist: user = None
            if user:
                login(request, user)
                del request.session['2fa_user_id'], request.session['2fa_code'], request.session['2fa_expiry']
                try: send_mail('AlignEd Admin Panel: Successful Login', f"The user '{user.username}' successfully logged in.", settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])
                except Exception as e: print(f"Error sending login email: {e}")
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid verification code.')
            return render(request, 'recommender/login.html', {'awaiting_2fa': True})
    if request.method == 'POST' and 'username' in request.POST:
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None and user.is_superuser:
            grace_period_key = f'grace_period_user_{user.id}'
            if cache.get(grace_period_key): login(request, user); cache.delete(grace_period_key); return redirect('admin_dashboard')
            code, expiry_time = str(random.randint(10000, 99999)), datetime.now() + timedelta(minutes=3)
            request.session['2fa_user_id'], request.session['2fa_code'], request.session['2fa_expiry'] = user.id, code, expiry_time.isoformat()
            try:
                send_mail('Your AlignEd Admin Login Code', f'Your verification code is: {code}', settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])
                messages.success(request, 'A verification code has been sent to your email.')
            except Exception as e: messages.error(request, 'Failed to send email.'); print(f"Error sending 2FA email: {e}")
            return render(request, 'recommender/login.html', {'awaiting_2fa': True})
        else: messages.error(request, 'Invalid credentials or not an admin account.')
    if '2fa_user_id' in request.session: del request.session['2fa_user_id']
    return render(request, 'recommender/login.html', {'awaiting_2fa': False})

def logout_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        logout(request)
        cache.set(f'grace_period_user_{user_id}', True, timeout=45)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('dashboard')

@user_passes_test(is_superuser)
def admin_dashboard_view(request):
    from django.db.models import Sum, F, Q, Count, Case, When, Value, IntegerField, Avg # Ensure Avg is imported
    
    total_assessments = Assessment.objects.count()
    feedback_assessments = Assessment.objects.filter(feedback_submitted=True)
    total_feedback_submissions = feedback_assessments.count()
    
    total_rating_sum_agg = feedback_assessments.aggregate(
        total_sum=Sum(F('feedback_rating_1') + F('feedback_rating_2') + F('feedback_rating_3'))
    )
    total_rating_sum = total_rating_sum_agg.get('total_sum') or 0

    total_rating_count_agg = feedback_assessments.aggregate(
        total_count=Sum(
            Case(When(feedback_rating_1__isnull=False, then=Value(1)), default=Value(0)) +
            Case(When(feedback_rating_2__isnull=False, then=Value(1)), default=Value(0)) +
            Case(When(feedback_rating_3__isnull=False, then=Value(1)), default=Value(0)),
            output_field=IntegerField()
        )
    )
    total_rating_count = total_rating_count_agg.get('total_count') or 0
    
    avg_user_satisfaction = (total_rating_sum / total_rating_count) if total_rating_count > 0 else 0
    total_possible_score = total_rating_count * 5
    overall_score_percentage = (total_rating_sum / total_possible_score * 100) if total_possible_score > 0 else 0
    
    r1_avg_result = feedback_assessments.aggregate(
        r1_avg=Avg('feedback_rating_1')
    )
    top_match_average_score = r1_avg_result.get('r1_avg') or 0
    
    top_courses = Assessment.objects.values('recommended_course_1').annotate(count=Count('recommended_course_1')).exclude(recommended_course_1__exact='').order_by('-count')[:5]
    assessments_by_strand = Assessment.objects.values('shs_strand').annotate(count=Count('shs_strand')).order_by('-count')
    
    context = {
        'active_page': 'admin_dashboard', 
        'total_assessments_count': total_assessments,
        'total_feedback_count': total_feedback_submissions,
        
        # FINAL METRICS: Aligned Naming
        'average_user_satisfaction': avg_user_satisfaction,             
        'overall_score_percentage': overall_score_percentage,
        'top_match_average_score': top_match_average_score,
        
        'top_recommended_courses': top_courses, 
        'assessments_by_strand': assessments_by_strand,
    }
    return render(request, 'recommender/admin_dashboard.html', context)

@user_passes_test(is_superuser)
def assessment_history_view(request):
    assessments_list = Assessment.objects.all()
    
    sort_by = request.GET.get('sort', '-timestamp')
    page_number = request.GET.get('page', 1)

    valid_sorts = ['-timestamp', 'timestamp', 'shs_strand', '-shs_strand']
    if sort_by not in valid_sorts:
        sort_by = '-timestamp' 
    
    selected_strand = request.GET.get('strand')
    if selected_strand and selected_strand != 'all':
        assessments_list = assessments_list.filter(shs_strand=selected_strand)
        
    date_filter = request.GET.get('date_filter')
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()

            assessments_list = assessments_list.filter(timestamp__gte=filter_date)
        except ValueError:
            pass 

    assessments_list = assessments_list.order_by(sort_by)
    paginator = Paginator(assessments_list, 10)

    try:
        assessments = paginator.page(page_number)
    except PageNotAnInteger:
        assessments = paginator.page(1)
    except EmptyPage:
        assessments = paginator.page(paginator.num_pages)
        
    all_strands = Assessment.objects.values_list('shs_strand', flat=True).distinct()
    
    context = {
        'active_page': 'assessment_history',
        'assessments': assessments, 
        'current_sort': sort_by,
        'all_strands': sorted(list(all_strands)),
        'selected_strand': selected_strand,
        'date_filter_value': date_filter,
    }
    return render(request, 'recommender/admin_assessment_history.html', context)

    
@user_passes_test(is_superuser)
def export_analytics_view(request):
    import csv # Lazy import
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assessment_analytics.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'School', 'SHS Strand', 'TVL Strand', 'Rec 1', 'Rec 2', 'Rec 3', 'Field Rec 1', 'Field Rec 2', 'Field Rec 3', 'Timestamp'])
    for assessment in Assessment.objects.all().values_list('id', 'name', 'school', 'shs_strand', 'tvl_strand', 'recommended_course_1', 'recommended_course_2', 'recommended_course_3', 'timestamp'): 
         writer.writerow(list(assessment[:-1]) + ['N/A', 'N/A', 'N/A'] + [assessment[-1]])
    return response

@user_passes_test(is_superuser)
def delete_all_assessments_view(request):
    if request.method == 'POST': Assessment.objects.all().delete()
    return redirect('admin_dashboard')

@user_passes_test(is_superuser)
def course_list_view(request):
    courses = Course.objects.all().order_by('name')
    context = {'active_page': 'course_list', 'courses': courses}
    return render(request, 'recommender/admin_course_list.html', context)

@user_passes_test(is_superuser)
def course_create_view(request):
    from .models import FIELD_CHOICES
    if request.method == 'POST':
        Course.objects.create(
            name=request.POST.get('name'), 
            description=request.POST.get('description'), 
            icon=request.POST.get('icon'),
            field_category=request.POST.get('field_category')
        )
        return redirect('course_list')
    context = {'action': 'Create', 'active_page': 'course_list', 'field_choices': FIELD_CHOICES}
    return render(request, 'recommender/admin_course_form.html', context)

@user_passes_test(is_superuser)
def course_update_view(request, pk):
    from .models import FIELD_CHOICES
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.name, course.description, course.icon = request.POST.get('name'), request.POST.get('description'), request.POST.get('icon')
        course.field_category = request.POST.get('field_category') # Save the new field
        course.save()
        return redirect('course_list')
    context = {'action': 'Update', 'course': course, 'active_page': 'course_list', 'field_choices': FIELD_CHOICES}
    return render(request, 'recommender/admin_course_form.html', context)

@user_passes_test(is_superuser)
def course_delete_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        return redirect('course_list')
    context = {'course': course, 'active_page': 'course_list'}
    return render(request, 'recommender/admin_course_confirm_delete.html', context)

@user_passes_test(is_superuser)
def export_analytics_pdf_view(request):
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    p.setFont("Helvetica-Bold", 16)
    p.drawString(inch, height - inch, "AlignEd System Analytics Report")
    p.setFont("Helvetica", 10)
    p.drawString(inch, height - 1.2 * inch, f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    p.line(inch, height - 1.3 * inch, width - inch, height - 1.3 * inch)
    
    total_assessments = Assessment.objects.count()
    feedback_count = Assessment.objects.filter(feedback_submitted=True).count()
    
    p.setFont("Helvetica", 12)
    p.drawString(inch, height - 1.8 * inch, f"Total Assessments Taken: {total_assessments}")
    p.drawString(inch, height - 2.0 * inch, f"Total Feedbacks Submitted: {feedback_count}")
    
    assessments_by_strand = Assessment.objects.values('shs_strand').annotate(count=Count('shs_strand')).order_by('-count')
    strands = [item['shs_strand'] for item in assessments_by_strand]
    counts = [item['count'] for item in assessments_by_strand]
    
    if strands:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.barh(strands, counts, color='#4F46E5')
        ax.set_xlabel('Number of Assessments')
        ax.set_title('Assessments by SHS Strand')
        ax.invert_yaxis()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        plt.close(fig)
        img_buffer.seek(0)
        image = ImageReader(img_buffer)
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(inch, height - 2.5 * inch, "Distribution of Assessments")
        p.drawImage(image, inch, height - 5.5 * inch, width=6*inch, height=3*inch)
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='AlignEd_Analytics_Report.pdf')