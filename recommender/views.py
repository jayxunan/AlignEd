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
from .models import Assessment, Course, University, PersonaTemplate, CoursePersonaWeight, UserProfile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import joblib 
import pandas as pd
from .forms import UserRegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import user_passes_test, login_required # <-- FIX THIS LINE
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout # Ensure this is imported at the top
from django.contrib.auth.decorators import login_required # Ensure this is imported
from .forms import UserSettingsForm
from .models import UserProfile, ProfileChangeToken


BASE_DIR = os.path.dirname(__file__)
FIELD_MODEL_PATH = os.path.join(BASE_DIR, 'field_model.joblib')
ENCODERS_PATH = os.path.join(BASE_DIR, 'label_encoders.joblib')

FIELD_MODEL = None
ENCODERS = None

try:
    FIELD_MODEL = joblib.load(FIELD_MODEL_PATH)
    ENCODERS = joblib.load(ENCODERS_PATH)
    print("SUCCESS: ML Models and Encoders loaded successfully at startup.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load ML models: {e}")

MASTER_TRAIT_LIST = [
    # Interests (25)
    'interest_research', 'interest_arts', 'interest_policy', 'interest_design', 
    'interest_tech', 'interest_building', 'interest_nature', 'interest_detail',
    'interest_leading', 'interest_helping', 'interest_tools', 'interest_analysis',
    'interest_writing', 'interest_performing', 'interest_health_care', 'interest_finance',
    'interest_sales', 'interest_education', 'interest_management', 'interest_marketing',
    'interest_performing_arts', 'interest_counseling', 'interest_social_service', 
    'interest_legal', 'interest_business',
    # Aptitudes & DMGT (25)
    'ability_logic', 'ability_creativity', 'ability_comm', 'ability_practical',
    'ability_teamwork', 'ability_spatial', 'ability_numerical', 'ability_abstract_reason',
    'ability_verbal_comp', 'ability_clerical', 'ability_mech_reason', 'ability_organization',
    'ability_detailcheck', 'ability_comprehension', 'ability_problem_solve',
    'dmgt_resilience', 'dmgt_persistence', 'dmgt_self_manage', 'dmgt_patience',
    'dmgt_flexibility', 'dmgt_integrity', 'dmgt_stress_manage', 'dmgt_initiative',
    'ability_comm_written', 'ability_negotiation'
]

COURSE_PERSONAS = {
    # -----------------------------------------------------
    # TECHNOLOGY, COMPUTING, & DATA
    # -----------------------------------------------------
    'Computer Science': {
        'key_traits': ['ability_logic', 'interest_tech', 'ability_numerical', 'dmgt_persistence'],
        'label': 'Logical Systems Builder',
        'profile': {
            'ability_logic': 5, 'interest_tech': 5, 'interest_research': 5, 'ability_numerical': 5, 'ability_abstract_reason': 4,
            'ability_creativity': 3, 'ability_practical': 4, 'dmgt_persistence': 4, 'ability_detailcheck': 4
        }
    },
    'Information Technology': {
        'key_traits': ['ability_practical', 'interest_tech', 'ability_teamwork', 'ability_logic'],
        'label': 'Practical Technologist',
        'profile': {
            'ability_practical': 5, 'interest_tech': 5, 'ability_teamwork': 4, 'ability_comm': 3, 'interest_building': 4,
            'ability_logic': 4, 'interest_management': 3, 'ability_organization': 4
        }
    },
    'Information Systems': {
        'key_traits': ['interest_detail', 'ability_logic', 'interest_business', 'interest_management'],
        'label': 'Tech-Business Integrator',
        'profile': {
            'interest_detail': 5, 'ability_logic': 4, 'interest_business': 4, 'interest_tech': 4, 'ability_teamwork': 3,
            'ability_numerical': 4, 'interest_management': 5, 'ability_organization': 5
        }
    },
    'Information Security': {
        'key_traits': ['ability_logic', 'interest_tech', 'ability_clerical', 'ability_detailcheck'],
        'label': 'Digital Defender',
        'profile': {
            'ability_logic': 5, 'interest_tech': 5, 'ability_detailcheck': 5, 'ability_clerical': 4, 'ability_practical': 3,
            'interest_leading': 3, 'interest_analysis': 5, 'dmgt_persistence': 4
        }
    },
    'Web & Mobile Development': {
        'key_traits': ['ability_creativity', 'ability_practical', 'interest_design', 'interest_tech'],
        'label': 'Creative Developer',
        'profile': {
            'ability_creativity': 5, 'ability_practical': 5, 'interest_design': 4, 'interest_tech': 5, 'ability_logic': 3,
            'interest_writing': 4, 'interest_arts': 4, 'interest_analysis': 3
        }
    },
    'Game Design & Development': {
        'key_traits': ['ability_creativity', 'ability_logic', 'interest_design', 'interest_performing_arts'],
        'label': 'Interactive Designer',
        'profile': {
            'ability_creativity': 5, 'ability_logic': 4, 'interest_design': 5, 'interest_arts': 4, 'interest_tech': 4,
            'interest_performing_arts': 4, 'ability_abstract_reason': 3
        }
    },
    'Data Science & Analytics': {
        'key_traits': ['ability_logic', 'ability_numerical', 'interest_research', 'ability_abstract_reason'],
        'label': 'Analytical Specialist',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'ability_numerical': 5, 'ability_abstract_reason': 5,
            'interest_detail': 4, 'interest_tech': 4, 'ability_comm': 3, 'interest_finance': 4
        }
    },
    'Business Analytics': {
        'key_traits': ['interest_business', 'ability_logic', 'ability_numerical', 'interest_finance'],
        'label': 'Business Strategist',
        'profile': {
            'interest_business': 5, 'ability_logic': 5, 'ability_numerical': 4, 'interest_finance': 5,
            'interest_detail': 4, 'interest_tech': 4, 'ability_comm': 3, 'interest_management': 4
        }
    },
    'Esports': {
        'key_traits': ['ability_teamwork', 'interest_leading', 'interest_tech', 'dmgt_persistence'],
        'label': 'Gaming Entrepreneur',
        'profile': {
            'ability_teamwork': 5, 'interest_leading': 4, 'interest_tech': 5, 'interest_business': 4,
            'dmgt_persistence': 4, 'interest_detail': 3, 'interest_management': 3, 'ability_organization': 4
        }
    },
    'Actuarial Science': {
        'key_traits': ['ability_logic', 'ability_numerical', 'interest_detail', 'interest_finance'],
        'label': 'Risk Mathematician',
        'profile': {
            'ability_logic': 5, 'interest_detail': 5, 'interest_research': 5, 'ability_numerical': 5,
            'interest_finance': 5, 'interest_business': 4, 'ability_clerical': 4
        }
    },
    'Applied Mathematics': {
        'key_traits': ['ability_logic', 'interest_research', 'ability_numerical', 'ability_abstract_reason'],
        'label': 'Quantitative Modeler',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'ability_numerical': 5, 'ability_abstract_reason': 5,
            'interest_tech': 4, 'interest_analysis': 5, 'dmgt_persistence': 4
        }
    },
    'Mathematics with Specializations (Business Application, Data Science)': {
        'key_traits': ['ability_logic', 'ability_numerical', 'interest_business', 'interest_finance'],
        'label': 'Applied Logician',
        'profile': {
            'ability_logic': 5, 'ability_numerical': 5, 'interest_business': 4, 'interest_finance': 4,
            'interest_research': 4, 'interest_tech': 4, 'interest_detail': 4
        }
    },
    
    # -----------------------------------------------------
    # ENGINEERING, ARCHITECTURE, & DESIGN
    # -----------------------------------------------------
    'Architecture': {
        'key_traits': ['ability_creativity', 'interest_design', 'ability_spatial', 'ability_practical'],
        'label': 'Creative Space Designer',
        'profile': {
            'ability_creativity': 5, 'interest_design': 5, 'ability_spatial': 5, 'ability_logic': 4,
            'interest_building': 4, 'ability_practical': 4
        }
    },
    'Interior Design': {
        'key_traits': ['ability_creativity', 'interest_design', 'ability_spatial', 'interest_arts'],
        'label': 'Indoor Space Stylist',
        'profile': {
            'ability_creativity': 5, 'interest_design': 5, 'interest_arts': 4, 'ability_spatial': 4,
            'ability_comm': 3, 'interest_building': 3
        }
    },
    'Industrial Engineering': {
        'key_traits': ['interest_business', 'ability_logic', 'ability_organization', 'interest_management'],
        'label': 'Efficiency Optimizer',
        'profile': {
            'interest_business': 5, 'ability_logic': 5, 'ability_organization': 5, 'interest_management': 5,
            'ability_teamwork': 4, 'ability_comm': 4, 'ability_practical': 3
        }
    },
    'Civil Engineering': {
        'key_traits': ['ability_practical', 'ability_logic', 'interest_building', 'ability_spatial'],
        'label': 'Structural Planner',
        'profile': {
            'ability_practical': 5, 'ability_logic': 5, 'interest_building': 4, 'ability_spatial': 4,
            'ability_numerical': 4, 'interest_research': 4
        }
    },
    'Computer Engineering': {
        'key_traits': ['ability_logic', 'interest_tech', 'interest_building', 'ability_numerical'],
        'label': 'Hardware Innovator',
        'profile': {
            'ability_logic': 5, 'interest_tech': 5, 'interest_building': 4, 'ability_practical': 4,
            'ability_numerical': 4, 'interest_research': 4
        }
    },
    'Electrical Engineering': {
        'key_traits': ['ability_logic', 'interest_tech', 'interest_building', 'ability_mech_reason'],
        'label': 'Power Systems Expert',
        'profile': {
            'ability_logic': 5, 'interest_tech': 5, 'interest_building': 4, 'ability_practical': 4,
            'ability_numerical': 4, 'interest_mech_reason': 5
        }
    },
    'Electronics Engineering': {
        'key_traits': ['ability_logic', 'interest_tech', 'interest_research', 'ability_numerical'],
        'label': 'Circuit Designer',
        'profile': {
            'ability_logic': 5, 'interest_tech': 5, 'interest_research': 4, 'ability_practical': 4,
            'ability_numerical': 4, 'interest_building': 3
        }
    },
    'Manufacturing & Robotics Engineering': {
        'key_traits': ['ability_practical', 'interest_building', 'interest_tech', 'ability_mech_reason'],
        'label': 'Robotics Production Lead',
        'profile': {
            'ability_practical': 5, 'interest_building': 5, 'interest_tech': 5, 'ability_logic': 4,
            'ability_teamwork': 4, 'interest_mech_reason': 5
        }
    },
    'Metallurgical Engineering': {
        'key_traits': ['interest_research', 'ability_practical', 'interest_building', 'interest_analysis'],
        'label': 'Metal Specialist',
        'profile': {
            'interest_research': 5, 'ability_practical': 5, 'interest_building': 4, 'ability_logic': 4,
            'interest_analysis': 4, 'interest_tools': 5
        }
    },
    'Construction Engineering & Management': {
        'key_traits': ['interest_building', 'ability_practical', 'interest_leading', 'interest_management'],
        'label': 'Project Site Leader',
        'profile': {
            'interest_building': 5, 'ability_practical': 5, 'interest_leading': 4, 'ability_teamwork': 4,
            'interest_business': 4, 'interest_management': 5
        }
    },
    'Geology & Geological Science and Engineering': {
        'key_traits': ['interest_nature', 'interest_research', 'ability_logic', 'ability_spatial'],
        'label': 'Earth Structure Analyst',
        'profile': {
            'interest_nature': 5, 'interest_research': 5, 'ability_logic': 4, 'ability_spatial': 4,
            'ability_practical': 3
        }
    },
    'Instrumentation & Control Engineering': {
        'key_traits': ['ability_logic', 'interest_tech', 'ability_practical', 'interest_tools'],
        'label': 'System Automator',
        'profile': {
            'ability_logic': 5, 'interest_tech': 5, 'ability_practical': 4, 'interest_building': 4,
            'interest_research': 3, 'interest_tools': 5
        }
    },
    'Transportation Engineering': {
        'key_traits': ['ability_logic', 'interest_building', 'ability_numerical', 'ability_abstract_reason'],
        'label': 'Traffic Flow Designer',
        'profile': {
            'ability_logic': 5, 'interest_building': 5, 'ability_numerical': 4, 'ability_practical': 4,
            'interest_tech': 3, 'ability_abstract_reason': 4
        }
    },

    # -----------------------------------------------------
    # BUSINESS, MANAGEMENT, & ECONOMICS (BUS)
    # -----------------------------------------------------
    'Accountancy': {
        'key_traits': ['ability_logic', 'interest_detail', 'ability_clerical', 'ability_numerical'],
        'label': 'Detail-Oriented Auditor',
        'profile': {
            'ability_logic': 5, 'interest_detail': 5, 'interest_business': 5, 'ability_clerical': 5,
            'ability_numerical': 5, 'ability_practical': 3, 'ability_comm': 2
        }
    },
    'Internal Auditing': {
        'key_traits': ['ability_logic', 'interest_detail', 'ability_clerical', 'interest_finance'],
        'label': 'Compliance Analyst',
        'profile': {
            'ability_logic': 5, 'interest_detail': 5, 'interest_business': 5, 'ability_clerical': 5,
            'interest_finance': 5, 'ability_teamwork': 3, 'ability_comm': 3
        }
    },
    'Business Administration': {
        'key_traits': ['ability_teamwork', 'interest_leading', 'interest_business', 'interest_management'],
        'label': 'Team Leader',
        'profile': {
            'ability_teamwork': 5, 'interest_leading': 5, 'interest_business': 5, 'ability_comm': 4,
            'interest_management': 5, 'ability_logic': 3
        }
    },
    'Entrepreneurship': {
        'key_traits': ['interest_leading', 'interest_business', 'ability_creativity', 'interest_sales'],
        'label': 'Innovative Founder',
        'profile': {
            'interest_leading': 5, 'interest_business': 5, 'ability_creativity': 5, 'interest_sales': 5,
            'interest_marketing': 4, 'ability_comm': 4, 'ability_logic': 3
        }
    },
    'Financial Management': {
        'key_traits': ['ability_logic', 'interest_finance', 'interest_detail', 'ability_numerical'],
        'label': 'Investment Planner',
        'profile': {
            'ability_logic': 5, 'interest_business': 5, 'interest_detail': 4, 'interest_finance': 5,
            'ability_numerical': 5, 'ability_comm': 3, 'interest_leading': 3
        }
    },
    'Marketing Management': {
        'key_traits': ['ability_creativity', 'ability_comm', 'interest_marketing', 'interest_sales'],
        'label': 'Creative Strategist',
        'profile': {
            'ability_creativity': 5, 'ability_comm': 5, 'interest_marketing': 5, 'interest_sales': 4,
            'interest_business': 4, 'interest_leading': 4, 'interest_design': 3
        }
    },
    'Operations Management (Business major)': {
        'key_traits': ['ability_practical', 'ability_organization', 'ability_logic', 'interest_detail'],
        'label': 'Process Optimizer',
        'profile': {
            'ability_practical': 5, 'ability_organization': 5, 'ability_logic': 4, 'interest_detail': 4,
            'interest_business': 4, 'ability_teamwork': 4
        }
    },
    'Applied Corporate Management': {
        'key_traits': ['interest_leading', 'interest_business', 'ability_teamwork', 'interest_management'],
        'label': 'Corporate Executive',
        'profile': {
            'interest_leading': 5, 'interest_business': 5, 'ability_teamwork': 4, 'ability_comm': 4,
            'interest_management': 5, 'ability_logic': 3
        }
    },
    'Economics': {
        'key_traits': ['ability_logic', 'interest_research', 'interest_policy', 'ability_numerical'],
        'label': 'Policy Analyst',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'interest_policy': 4, 'ability_numerical': 4,
            'interest_business': 4, 'ability_comm': 3
        }
    },
    'Business Economics': {
        'key_traits': ['ability_logic', 'interest_business', 'interest_research', 'ability_numerical'],
        'label': 'Market Predictor',
        'profile': {
            'ability_logic': 5, 'interest_business': 4, 'interest_research': 4, 'ability_numerical': 4,
            'ability_comm': 3, 'interest_leading': 3
        }
    },
    'Applied Economics': {
        'key_traits': ['ability_logic', 'interest_detail', 'interest_business', 'ability_numerical'],
        'label': 'Economic Modeler',
        'profile': {
            'ability_logic': 5, 'interest_detail': 5, 'interest_business': 4, 'interest_research': 4,
            'ability_numerical': 5, 'interest_policy': 3
        }
    },
    'Real Estate': {
        'key_traits': ['interest_business', 'ability_comm', 'interest_detail', 'interest_sales'],
        'label': 'Property Strategist',
        'profile': {
            'interest_business': 5, 'ability_comm': 5, 'interest_detail': 4, 'interest_leading': 4,
            'interest_sales': 5, 'ability_logic': 3
        }
    },
    
    # -----------------------------------------------------
    # HEALTH, LIFE, & NATURAL SCIENCES (HEALTH)
    # -----------------------------------------------------
    'Medicine': {
        'key_traits': ['interest_helping', 'interest_research', 'ability_logic', 'ability_verbal_comp'],
        'label': 'Medical Physician',
        'profile': {
            'interest_helping': 5, 'interest_research': 5, 'ability_logic': 5, 'ability_verbal_comp': 4,
            'ability_comm': 4, 'interest_health_care': 5, 'dmgt_persistence': 5
        }
    },
    'Nursing': {
        'key_traits': ['interest_helping', 'ability_comm', 'ability_teamwork', 'interest_health_care'],
        'label': 'Empathetic Caregiver',
        'profile': {
            'interest_helping': 5, 'ability_comm': 5, 'ability_teamwork': 5, 'interest_health_care': 5,
            'interest_research': 4, 'ability_practical': 3, 'dmgt_patience': 5
        }
    },
    'Medical Technology': {
        'key_traits': ['ability_logic', 'interest_research', 'ability_practical', 'ability_detailcheck'],
        'label': 'Lab Analyst',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'ability_practical': 4, 'interest_detail': 4,
            'ability_detailcheck': 5, 'interest_health_care': 4
        }
    },
    'Pharmaceutical Sciences': {
        'key_traits': ['ability_logic', 'interest_research', 'ability_detailcheck', 'interest_health_care'],
        'label': 'Drug Formulation Expert',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'interest_detail': 4, 'ability_detailcheck': 5,
            'interest_health_care': 5, 'ability_practical': 3
        }
    },
    'Nutrition & Dietetics': {
        'key_traits': ['interest_helping', 'ability_comm', 'interest_health_care', 'interest_research'],
        'label': 'Wellness Coach',
        'profile': {
            'interest_helping': 5, 'interest_research': 4, 'ability_comm': 5, 'interest_health_care': 5,
            'ability_logic': 3, 'ability_practical': 3
        }
    },
    'Health Professions': {
        'key_traits': ['interest_helping', 'ability_teamwork', 'interest_health_care', 'ability_organization'],
        'label': 'Healthcare Coordinator',
        'profile': {
            'interest_helping': 5, 'interest_research': 4, 'ability_teamwork': 4, 'ability_comm': 4,
            'interest_health_care': 5, 'ability_organization': 4
        }
    },
    'Clinical Audiology': {
        'key_traits': ['interest_helping', 'interest_research', 'ability_detailcheck', 'ability_comm'],
        'label': 'Hearing Specialist',
        'profile': {
            'interest_helping': 5, 'interest_research': 4, 'ability_detailcheck': 4, 'ability_logic': 4,
            'ability_comm': 4
        }
    },
    'Clinical Pharmacy': {
        'key_traits': ['ability_logic', 'interest_research', 'interest_helping', 'ability_detailcheck'],
        'label': 'Patient Drug Expert',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'interest_helping': 4, 'ability_comm': 4,
            'ability_detailcheck': 5
        }
    },
    'Human Biology': {
        'key_traits': ['interest_research', 'ability_logic', 'ability_verbal_comp', 'interest_health_care'],
        'label': 'Human Life Scientist',
        'profile': {
            'interest_research': 5, 'ability_logic': 5, 'ability_verbal_comp': 4, 'interest_health_care': 4,
            'ability_practical': 4, 'dmgt_persistence': 4
        }
    },
    'Biology': {
        'key_traits': ['interest_research', 'ability_logic', 'interest_nature', 'ability_verbal_comp'],
        'label': 'Life Scientist',
        'profile': {
            'interest_research': 5, 'ability_logic': 5, 'interest_nature': 4, 'ability_practical': 3,
            'ability_verbal_comp': 4
        }
    },
    'Biochemistry': {
        'key_traits': ['interest_research', 'ability_logic', 'interest_detail', 'interest_analysis'],
        'label': 'Molecular Analyst',
        'profile': {
            'interest_research': 5, 'ability_logic': 5, 'interest_detail': 4, 'interest_analysis': 5,
            'ability_practical': 4, 'dmgt_persistence': 5
        }
    },
    'Biotechnology': {
        'key_traits': ['interest_research', 'ability_logic', 'interest_tech', 'interest_analysis'],
        'label': 'Cellular Innovator',
        'profile': {
            'interest_research': 5, 'ability_logic': 5, 'interest_tech': 4, 'interest_analysis': 5,
            'ability_practical': 4, 'ability_teamwork': 3
        }
    },
    'Chemistry': {
        'key_traits': ['interest_research', 'ability_logic', 'ability_practical', 'interest_analysis'],
        'label': 'Substance Analyst',
        'profile': {
            'interest_research': 5, 'ability_logic': 5, 'ability_practical': 4, 'interest_analysis': 5,
            'interest_building': 3
        }
    },
    'Physics': {
        'key_traits': ['ability_logic', 'interest_research', 'ability_abstract_reason', 'ability_numerical'],
        'label': 'Theoretical Thinker',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'ability_abstract_reason': 5, 'ability_numerical': 5,
            'interest_tech': 4, 'interest_building': 3
        }
    },
    'Applied Physics': {
        'key_traits': ['ability_logic', 'interest_tech', 'ability_practical', 'ability_numerical'],
        'label': 'Practical Engineer',
        'profile': {
            'ability_logic': 5, 'interest_tech': 5, 'ability_practical': 4, 'ability_numerical': 4,
            'interest_research': 4, 'interest_building': 3
        }
    },
    'Medical Physics': {
        'key_traits': ['ability_logic', 'interest_research', 'interest_helping', 'interest_health_care'],
        'label': 'Medical Device Specialist',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'interest_helping': 4, 'interest_health_care': 5,
            'interest_tech': 4, 'ability_practical': 3
        }
    },
    'Zoology / Systematics & Ecology': {
        'key_traits': ['interest_nature', 'interest_research', 'ability_logic', 'ability_detailcheck'],
        'label': 'Animal Classifier',
        'profile': {
            'interest_nature': 5, 'interest_research': 5, 'ability_logic': 4, 'ability_detailcheck': 4,
            'ability_practical': 3, 'interest_helping': 3
        }
    },
    'Veterinary or Animal Sciences': {
        'key_traits': ['interest_nature', 'interest_helping', 'ability_practical', 'interest_health_care'],
        'label': 'Animal Care Specialist',
        'profile': {
            'interest_nature': 5, 'interest_helping': 5, 'ability_practical': 4, 'interest_health_care': 4,
            'interest_research': 3, 'ability_teamwork': 4
        }
    },
    'Dentistry': {
        'key_traits': ['interest_helping', 'ability_practical', 'ability_detailcheck', 'dmgt_patience'],
        'label': 'Oral Health Expert',
        'profile': {
            'interest_helping': 5, 'ability_practical': 5, 'ability_detailcheck': 4, 'interest_detail': 4,
            'dmgt_patience': 5, 'ability_logic': 4
        }
    },
    
    # -----------------------------------------------------
    # SOCIAL SCIENCES, HUMANITIES, & LIBERAL ARTS (SOCIAL)
    # -----------------------------------------------------
    'Psychology': {
        'key_traits': ['ability_comm', 'interest_helping', 'interest_research', 'dmgt_patience'],
        'label': 'Insightful Advisor',
        'profile': {
            'ability_comm': 5, 'interest_helping': 5, 'interest_research': 4, 'dmgt_patience': 5,
            'ability_logic': 3, 'interest_education': 3
        }
    },
    'Clinical Psychology': {
        'key_traits': ['interest_helping', 'interest_research', 'ability_comm', 'interest_counseling'],
        'label': 'Mental Health Therapist',
        'profile': {
            'interest_helping': 5, 'interest_research': 5, 'ability_comm': 4, 'ability_logic': 4,
            'interest_policy': 3, 'interest_counseling': 5
        }
    },
    'Political Science': {
        'key_traits': ['interest_policy', 'ability_comm', 'ability_logic', 'interest_research'],
        'label': 'Government Analyst',
        'profile': {
            'interest_policy': 5, 'ability_comm': 5, 'ability_logic': 4, 'interest_leading': 4,
            'interest_research': 4
        }
    },
    'Legal Studies (Law)': {
        'key_traits': ['ability_logic', 'interest_policy', 'ability_verbal_comp', 'interest_legal'],
        'label': 'Rule Interpreter',
        'profile': {
            'ability_logic': 5, 'interest_policy': 5, 'ability_comm': 5, 'interest_detail': 4,
            'ability_verbal_comp': 5, 'interest_legal': 5
        }
    },
    'Public Administration': {
        'key_traits': ['interest_leading', 'interest_policy', 'ability_comm', 'ability_organization'],
        'label': 'Policy Implementer',
        'profile': {
            'interest_leading': 5, 'interest_policy': 5, 'ability_comm': 4, 'ability_logic': 4,
            'ability_organization': 5
        }
    },
    'International Studies': {
        'key_traits': ['interest_policy', 'ability_comm', 'interest_research', 'interest_arts'],
        'label': 'Global Diplomat',
        'profile': {
            'interest_policy': 5, 'ability_comm': 5, 'interest_arts': 4, 'interest_leading': 4,
            'interest_research': 4
        }
    },
    'Philippine Studies': {
        'key_traits': ['interest_arts', 'interest_research', 'ability_comm', 'ability_verbal_comp'],
        'label': 'Filipino Culture Scholar',
        'profile': {
            'interest_arts': 5, 'interest_research': 4, 'ability_comm': 4, 'ability_verbal_comp': 5,
            'interest_policy': 3
        }
    },
    'Asian Studies': {
        'key_traits': ['interest_research', 'interest_arts', 'ability_comm', 'ability_organization'],
        'label': 'Regional Expert',
        'profile': {
            'interest_research': 5, 'interest_arts': 4, 'ability_comm': 4, 'ability_organization': 4,
            'interest_policy': 3
        }
    },
    'Linguistics': {
        'key_traits': ['ability_logic', 'interest_research', 'ability_comm', 'ability_verbal_comp'],
        'label': 'Language Scientist',
        'profile': {
            'ability_logic': 5, 'interest_research': 4, 'ability_comm': 4, 'ability_verbal_comp': 5,
            'interest_arts': 3, 'interest_tech': 3
        }
    },
    'Social Sciences': {
        'key_traits': ['interest_helping', 'interest_research', 'ability_logic', 'interest_policy'],
        'label': 'Human Behavior Analyst',
        'profile': {
            'interest_helping': 5, 'interest_research': 4, 'ability_logic': 4, 'ability_comm': 4,
            'interest_policy': 3
        }
    },
    'Archaeology / Archaeological Studies': {
        'key_traits': ['interest_research', 'interest_nature', 'ability_detailcheck', 'ability_logic'],
        'label': 'Historical Detective',
        'profile': {
            'interest_research': 5, 'interest_nature': 5, 'interest_detailcheck': 4, 'ability_logic': 3,
            'ability_practical': 3
        }
    },

    # -----------------------------------------------------
    # COMMUNICATION, MEDIA, & CREATIVE ARTS (MEDIA)
    # -----------------------------------------------------
    'Broadcasting': {
        'key_traits': ['ability_comm', 'ability_creativity', 'interest_tech', 'interest_performing_arts'],
        'label': 'Media Producer',
        'profile': {
            'ability_comm': 5, 'ability_creativity': 5, 'interest_tech': 4, 'interest_arts': 4,
            'interest_leading': 3, 'interest_performing_arts': 5
        }
    },
    'Journalism': {
        'key_traits': ['ability_comm', 'interest_policy', 'interest_research', 'interest_writing'],
        'label': 'Investigative Reporter',
        'profile': {
            'ability_comm': 5, 'interest_policy': 4, 'interest_research': 4, 'interest_writing': 5,
            'ability_logic': 3
        }
    },
    'Advertising': {
        'key_traits': ['ability_creativity', 'interest_design', 'interest_marketing', 'interest_sales'],
        'label': 'Persuasion Strategist',
        'profile': {
            'ability_creativity': 5, 'interest_design': 5, 'interest_marketing': 5, 'interest_sales': 4,
            'interest_business': 4, 'ability_comm': 4
        }
    },
    'Digital Film & Media Production': {
        'key_traits': ['ability_creativity', 'interest_design', 'interest_tech', 'interest_performing_arts'],
        'label': 'Visual Storyteller',
        'profile': {
            'ability_creativity': 5, 'interest_design': 5, 'interest_tech': 4, 'interest_arts': 4,
            'interest_performing_arts': 4, 'ability_teamwork': 3
        }
    },
    'Multimedia Arts': {
        'key_traits': ['ability_creativity', 'interest_design', 'interest_arts', 'interest_tech'],
        'label': 'Creative Visualizer',
        'profile': {
            'ability_creativity': 5, 'interest_design': 5, 'interest_arts': 4, 'interest_tech': 4,
            'ability_practical': 3
        }
    },
    'Arts': {
        'key_traits': ['ability_creativity', 'interest_arts', 'interest_design', 'interest_writing'],
        'label': 'Creative Master',
        'profile': {
            'ability_creativity': 5, 'interest_arts': 5, 'interest_design': 5, 'interest_writing': 5,
            'ability_logic': 2
        }
    },
    'Theatre & Performance': {
        'key_traits': ['ability_creativity', 'ability_comm', 'interest_arts', 'interest_performing_arts'],
        'label': 'Performance Artist',
        'profile': {
            'ability_creativity': 5, 'ability_comm': 5, 'interest_arts': 5, 'interest_performing_arts': 5,
            'ability_teamwork': 4
        }
    },
    'Creative Writing': {
        'key_traits': ['ability_creativity', 'interest_arts', 'ability_comm', 'interest_writing'],
        'label': 'Literary Visionary',
        'profile': {
            'ability_creativity': 5, 'interest_arts': 5, 'ability_comm': 4, 'interest_writing': 5,
            'interest_research': 4, 'ability_logic': 3
        }
    },
    'Mass Communication & Organizational Communication': {
        'key_traits': ['ability_comm', 'interest_leading', 'interest_business', 'ability_organization'],
        'label': 'Corporate Communicator',
        'profile': {
            'ability_comm': 5, 'interest_leading': 4, 'interest_business': 4, 'ability_teamwork': 4,
            'ability_organization': 4
        }
    },
    'Voice & Vocal Performance': {
        'key_traits': ['interest_arts', 'ability_creativity', 'ability_comm', 'interest_performing_arts'],
        'label': 'Vocal Performer',
        'profile': {
            'interest_arts': 5, 'ability_creativity': 5, 'ability_comm': 4, 'interest_performing_arts': 5
        }
    },
    
    # -----------------------------------------------------
    # EDUCATION & LIBRARY SCIENCE (EDUC)
    # -----------------------------------------------------
    'Education': {
        'key_traits': ['interest_education', 'ability_comm', 'interest_helping', 'dmgt_patience'],
        'label': 'Inspirational Mentor',
        'profile': {
            'interest_education': 5, 'ability_comm': 5, 'interest_helping': 4, 'ability_teamwork': 4,
            'dmgt_patience': 5, 'ability_creativity': 3
        }
    },
    'Art Education': {
        'key_traits': ['interest_arts', 'interest_education', 'ability_creativity', 'ability_comm'],
        'label': 'Creative Instructor',
        'profile': {
            'interest_arts': 5, 'interest_education': 5, 'ability_creativity': 5, 'ability_comm': 4,
            'ability_teamwork': 3
        }
    },
    'Educational Psychology': {
        'key_traits': ['interest_education', 'interest_research', 'interest_helping', 'interest_counseling'],
        'label': 'Learning Behavior Specialist',
        'profile': {
            'interest_education': 5, 'interest_research': 4, 'interest_helping': 4, 'ability_logic': 4,
            'interest_counseling': 5, 'ability_comm': 4
        }
    },

    # -----------------------------------------------------
    # PUBLIC SERVICE & ADMINISTRATION (PUB)
    # -----------------------------------------------------
    'Public Administration': {
        'key_traits': ['interest_leading', 'interest_policy', 'ability_comm', 'ability_organization'],
        'label': 'Policy Implementer',
        'profile': {
            'interest_leading': 5, 'interest_policy': 5, 'ability_comm': 4, 'ability_logic': 4,
            'ability_organization': 5, 'interest_business': 3
        }
    },
    'Community Development': {
        'key_traits': ['interest_helping', 'ability_teamwork', 'interest_policy', 'interest_social_service'],
        'label': 'Grassroots Organizer',
        'profile': {
            'interest_helping': 5, 'ability_teamwork': 5, 'interest_policy': 4, 'ability_comm': 4,
            'interest_social_service': 5, 'interest_education': 3
        }
    },
    
    # -----------------------------------------------------
    # HOSPITALITY, TOURISM, & SERVICE INDUSTRIES (HOSP)
    # -----------------------------------------------------
    'Tourism Management': {
        'key_traits': ['ability_comm', 'interest_helping', 'interest_leading', 'interest_management'],
        'label': 'Travel Planner',
        'profile': {
            'ability_comm': 5, 'interest_helping': 4, 'interest_leading': 4, 'interest_management': 4,
            'interest_marketing': 4, 'interest_business': 3
        }
    },
    'Hotel, Restaurant & Institutional Management': {
        'key_traits': ['interest_helping', 'interest_business', 'ability_practical', 'ability_organization'],
        'label': 'Service Operations Leader',
        'profile': {
            'interest_helping': 5, 'interest_business': 4, 'ability_practical': 4, 'interest_leading': 4,
            'ability_teamwork': 5, 'ability_organization': 5
        }
    },
    'Cruise Line Operations': {
        'key_traits': ['interest_helping', 'ability_teamwork', 'ability_practical', 'interest_management'],
        'label': 'Maritime Service Specialist',
        'profile': {
            'interest_helping': 5, 'ability_teamwork': 5, 'ability_practical': 4, 'ability_comm': 4,
            'interest_management': 4
        }
    },

    # -----------------------------------------------------
    # APPLIED, TECHNICAL, & VOCATIONAL SCIENCES (APPLIED)
    # -----------------------------------------------------
    'Forensic': {
        'key_traits': ['ability_logic', 'interest_research', 'ability_detailcheck', 'interest_policy'],
        'label': 'Crime Scene Analyst',
        'profile': {
            'ability_logic': 5, 'interest_research': 5, 'ability_practical': 4, 'interest_policy': 4,
            'ability_detailcheck': 5
        }
    },
    'Criminology': {
        'key_traits': ['ability_logic', 'interest_policy', 'interest_leading', 'interest_detailcheck'],
        'label': 'Justice Investigator',
        'profile': {
            'ability_logic': 5, 'interest_policy': 5, 'interest_leading': 4, 'ability_comm': 4,
            'ability_practical': 3, 'ability_detailcheck': 5
        }
    },
    'Geology & Geological Science and Engineering': {
        'key_traits': ['interest_nature', 'interest_research', 'ability_logic', 'ability_spatial'],
        'label': 'Earth Structure Analyst',
        'profile': {
            'interest_nature': 5, 'interest_research': 5, 'ability_logic': 4, 'ability_spatial': 4,
            'ability_practical': 3
        }
    },
    'Vehicle/Automotive Engineering Technology': {
        'key_traits': ['ability_practical', 'interest_building', 'interest_tech', 'ability_mech_reason'],
        'label': 'Hands-on Technician',
        'profile': {
            'ability_practical': 5, 'interest_building': 5, 'interest_tech': 4, 'ability_logic': 3,
            'ability_teamwork': 3, 'interest_mech_reason': 5
        }
    },
    'Apparel and Fashion Technology': {
        'key_traits': ['ability_practical', 'interest_design', 'interest_arts', 'interest_detailcheck'],
        'label': 'Garment Engineer',
        'profile': {
            'ability_practical': 5, 'interest_design': 5, 'interest_arts': 4, 'ability_creativity': 4,
            'ability_detailcheck': 4, 'interest_business': 3
        }
    },
    'Industrial Arts': {
        'key_traits': ['ability_practical', 'interest_building', 'interest_tools', 'ability_mech_reason'],
        'label': 'Skilled Craftsman',
        'profile': {
            'ability_practical': 5, 'interest_building': 5, 'interest_tools': 5, 'ability_logic': 3,
            'ability_teamwork': 3, 'interest_mech_reason': 5
        }
    },
    'Applied Science — Laboratory Technology (BAS-LT)': {
        'key_traits': ['interest_research', 'ability_practical', 'ability_detailcheck', 'interest_analysis'],
        'label': 'Lab Technician',
        'profile': {
            'interest_research': 5, 'ability_practical': 5, 'ability_detailcheck': 5, 'ability_logic': 4,
            'interest_analysis': 4
        }
    },
    'Marine / Maritime-related': {
        'key_traits': ['interest_nature', 'interest_building', 'ability_practical', 'ability_teamwork'],
        'label': 'Seafaring Professional',
        'profile': {
            'interest_nature': 5, 'interest_building': 4, 'ability_practical': 4, 'ability_teamwork': 4,
            'interest_tech': 3
        }
    },
    'Human Kinetics': {
        'key_traits': ['ability_practical', 'interest_sports', 'interest_education', 'interest_health_care'],
        'label': 'Movement Specialist',
        'profile': {
            'ability_practical': 5, 'interest_sports': 5, 'interest_education': 4, 'interest_health_care': 4,
            'ability_comm': 3
        }
    },
}

ASSESSMENT_QUESTION_MAP = {

    "ability_numerical": "I am confident in solving complex calculations and numerical problems.",
    "ability_abstract_reason": "I am good at finding logical patterns in sequences of shapes or numbers.",
    "ability_verbal_comp": "I quickly understand complex written instructions or technical documents.",
    "ability_clerical": "I am very careful at whatever I do (Clerical Speed/Accuracy).",
    "ability_mech_reason": "I can follow a complex diagram or instructions to build something.",
    "ability_organization": "I make plans and stick to them (Systematic/Organized).",
    "ability_detailcheck": "I am confident in finding small errors or discrepancies in a long document.",
    "ability_comprehension": "I quickly grasp the main idea when reading complex academic articles.",
    "dmgt_persistence": "I keep trying even after I fail (Persistence).",
    "dmgt_self_manage": "I think carefully before I act (Self-Management).",

    "interest_research": "I enjoy technical research, analysis, and experiments.",
    "interest_tech": "I enjoy using software, coding, or managing technical systems.",
    "interest_building": "I enjoy manual work like building, repairing, or assembly.",
    "interest_nature": "I enjoy working outdoors, with plants, animals, or the environment.",
    "ability_spatial": "I am confident in mentally manipulating 3D objects (Spatial Aptitude).",
    "interest_tools": "I would enjoy installing an alarm system in a building.",
    "interest_analysis": "I would enjoy analyzing the structure of molecules.",
    "interest_writing": "I enjoy writing scripts, reports, or articles for a public audience.",
    "interest_performing": "I enjoy composing a song or performing on stage.",
    "interest_health_care": "I would enjoy doing laboratory tests to diagnose diseases.",

    "interest_detail": "I am good at handling complex financial records, numbers, or budgets.",
    "interest_leading": "I enjoy managing projects, organizing people, or taking charge of events.",
    "interest_helping": "I enjoy counseling, mentoring, or providing direct service to people.",
    "ability_teamwork": "I am good at collaborating effectively in diverse groups.",
    "interest_finance": "I would enjoy calculating the cost of an insurance claim.",
    "interest_sales": "I would enjoy persuading others to my point of view (Enterprising).",
    "interest_education": "I would enjoy tutoring a child or teaching adults new skills.",
    "interest_management": "I would enjoy leading a team and coordinating a business conference.",
    "interest_marketing": "I would enjoy planning a marketing strategy for a new company.",
    "dmgt_resilience": "I know I can get through bad times (Resilience).",

    "ability_logic": "Logical thinking and solving difficult abstract or numerical problems.",
    "ability_creativity": "Developing original ideas, solutions, or artistic concepts.",
    "ability_comm": "Verbal and written communication (Clarity of Expression).",
    "ability_practical": "Applying knowledge to mechanical tasks and using hands-on skills.",
    "interest_arts": "I enjoy painting, sculpting, or drawing (Artistic expression).",
    "interest_policy": "I enjoy studying history, social issues, governance, or international affairs.",
    "interest_social_service": "I would enjoy helping a needy family find appropriate housing.",
    "interest_legal": "I would enjoy reading legal documents and researching laws.",
    "dmgt_patience": "I remain calm and patient when a complicated task requires many attempts.",
    "interest_performing_arts": "I would enjoy performing musical theater or acting.",

    "ability_problem_solve": "I consider the positives and negatives of every option when I am making a decision.",
    "dmgt_integrity": "I stand up for what is right, even when I am scared.",
    "dmgt_flexibility": "If someone hurts me, but they say they're sorry, I forgive them.",
    "dmgt_initiative": "I am a very loyal member of my group.",
    "ability_comm_written": "I am good at finding the best word to complete a difficult sentence.",
    "ability_negotiation": "I am confident in negotiating with others to reach a deal.",

    "ability_numerical_b": "I easily solve problems that involve percentages.",
    "ability_numerical_c": "I can understand and turn a math problem written in words into numbers and symbols.",
    "ability_numerical_d": "I understand numbers that are written with powers of 10 (like 10⁵).",
    "ability_numerical_e": "I find it easy to calculate amounts when a recipe or mixture uses ratios.",
    
    "interest_business": "I often think about starting my own small business or company.", 
    "interest_science": "I enjoy reading about chemistry, physics, or biology in my free time.", 
    "interest_teaching": "I am good at explaining complicated concepts to others.", 
}


def get_recommendations_from_assessment(assessment):
    all_courses = Course.objects.all().prefetch_related('offering_universities')

    user_ratings = {trait: getattr(assessment, trait, 0) for trait in MASTER_TRAIT_LIST}

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

@login_required(login_url='/user/login/')
def user_settings_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, "Profile not found. Please log in or contact support.")
        return redirect('user_logout')

    initial_data = {
        'name': profile.name,
        'email': request.user.email,
        'age': profile.age,
        'strand': profile.strand,
        'university': profile.university,
        'year_level': profile.year_level
    }

    if request.method == 'POST':

        form = UserSettingsForm(request.POST, instance=profile)
        
        if form.is_valid():
            pending_data = form.cleaned_data

            new_password = pending_data.pop('new_password', None)
            pending_data.pop('confirm_password', None) 
            
            password_changed = False
            if new_password:
                pending_data['new_password'] = new_password
                password_changed = True

            changes_detected = False

            if str(pending_data.get('email')) != str(request.user.email):
                changes_detected = True

            profile_fields = ['name', 'age', 'strand', 'university', 'year_level']
            
            for field in profile_fields:
                new_value = pending_data.get(field)
                current_value = initial_data.get(field) 
                
                if str(new_value) != str(current_value):
                    changes_detected = True
                    break 
            if not (changes_detected or password_changed):
                messages.warning(request, "No changes detected.")
                return redirect('user_settings')

            code = str(random.randint(10000, 99999))
            secure_recipient_email = request.user.email 
            
            ProfileChangeToken.objects.filter(user=request.user).delete() 
            ProfileChangeToken.objects.create(
                user=request.user,
                pending_data=json.dumps(pending_data), 
                verification_code=code
            )
            
            try:
                send_mail(
                    'Profile Update Verification Code',
                    f'Your 5-digit verification code to confirm your profile update is: {code}',
                    settings.ADMIN_EMAIL,
                    [secure_recipient_email] 
                )
                request.session['pending_email'] = secure_recipient_email 
                messages.info(request, f"A verification code has been sent to your registered email ({secure_recipient_email}). Please check your inbox to confirm changes.")
                
                return render(request, 'recommender/user_settings_confirm.html', {'email': secure_recipient_email})

            except Exception as e:
                messages.error(request, f"Failed to send verification email. Error: {e}")
                
    else:
        form = UserSettingsForm(instance=profile)

    context = {'form': form, 'user_email': request.user.email} 
    return render(request, 'recommender/user_settings.html', context)


@login_required(login_url='/user/login/')
def confirm_verification_view(request):
    
    recipient_email = request.session.get('pending_email', request.user.email)

    if request.method == 'POST':
        user_code = request.POST.get('verification_code')
        
        try:
            token = ProfileChangeToken.objects.get(user=request.user, verification_code=user_code)
            
            pending_data = json.loads(token.pending_data)

            if request.user.email != pending_data.get('email'):
                request.user.email = pending_data.get('email')

            new_password = pending_data.get('new_password')
            if new_password:
                request.user.set_password(new_password) 
                
            request.user.save() 

            profile = request.user.userprofile
            profile.name = pending_data['name']
            profile.age = pending_data['age']
            profile.strand = pending_data['strand']
            profile.university = pending_data['university']
            profile.year_level = pending_data['year_level']
            profile.save()
            
            # 3. Clean up
            token.delete()
            if 'pending_email' in request.session:
                del request.session['pending_email']
            
            messages.success(request, "Your profile changes have been successfully saved!")
            return redirect('user_settings')
            
        except ProfileChangeToken.DoesNotExist:
            messages.error(request, "Invalid or expired verification code.")
            
    context = {'email': recipient_email}
    return render(request, 'recommender/user_settings_confirm.html', context)

@login_required(login_url='/user/login/')
def email_recommendations_view(request, assessment_id):
    if request.method == 'POST':
        if not request.user.email:
            messages.error(request, "Your registered account is missing an email address.")
            return redirect('recommendation_result_with_id', assessment_id=assessment_id)
            
        recipient_email = request.user.email

        try:
            assessment = get_object_or_404(Assessment, id=assessment_id)
            
            if assessment.user != request.user:
                messages.error(request, "Unauthorized access to assessment data.")
                return redirect('dashboard')

            recommendations = get_recommendations_from_assessment(assessment)

            email_context = {
                'recommendations': recommendations,
                'student_name': assessment.display_name or 'Valued User',
                'timestamp': assessment.timestamp.strftime("%B %d, %Y"),
                'is_email_view': True
            }
            html_message = render_to_string('recommender/email/recommendation_email.html', email_context)
            
            # 3. Send the email
            subject = 'Your AlignEd Course Recommendation Results'
            
            email = EmailMessage(
                subject,
                html_message,
                settings.ADMIN_EMAIL,
                [recipient_email]
            )
            email.content_subtype = "html"
            email.send()

            messages.success(request, f"Your results have been sent to {recipient_email}!")
            return redirect('recommendation_result_with_id', assessment_id=assessment_id)

        except Assessment.DoesNotExist:
            messages.error(request, "Assessment record not found.")
            return redirect('assessment')
        except Exception as e:
            messages.error(request, "Failed to send email. Check your server logs for details.")
            print(f"EMAIL SEND ERROR: {e}") 
            return redirect('recommendation_result_with_id', assessment_id=assessment_id)
            
    return redirect('recommendation_result_with_id', assessment_id=assessment_id)

def get_in_depth_insights(course_name, user_ratings):
    TRAIT_LABEL_MAP = {
        'ability_logic': 'Logical Thinking', 
        'ability_creativity': 'Creativity', 
        'ability_comm': 'Verbal Communication', 
        'ability_practical': 'Practical Skills', 
        'ability_teamwork': 'Teamwork', 
        'ability_spatial': 'Spatial Reasoning',
        'ability_numerical': 'Numerical Aptitude',
        'ability_abstract_reason': 'Abstract Reasoning', 
        'ability_verbal_comp': 'Verbal Comprehension',
        'ability_clerical': 'Clerical Accuracy', 
        'ability_mech_reason': 'Mechanical Reasoning', 
        'ability_organization': 'Organization',
        'ability_detailcheck': 'Attention to Detail', 
        'ability_comprehension': 'Reading Comprehension', 
        'ability_problem_solve': 'Problem Solving',
        'dmgt_resilience': 'Resilience', 
        'dmgt_persistence': 'Persistence', 
        'dmgt_self_manage': 'Self-Management', 
        'dmgt_patience': 'Patience',
        'dmgt_flexibility': 'Flexibility/Adaptability', 
        'dmgt_integrity': 'Integrity', 
        'dmgt_stress_manage': 'Stress Management',
        'dmgt_initiative': 'Initiative',
        'ability_comm_written': 'Written Expression', 
        'ability_negotiation': 'Negotiation Skill',
        'interest_research': 'Research/Investigative', 
        'interest_arts': 'Fine Arts', 
        'interest_policy': 'Social Policy/Governance', 
        'interest_design': 'Aesthetic Design',
        'interest_tech': 'Technology', 
        'interest_building': 'Construction/Building', 
        'interest_nature': 'Nature/Environment', 
        'interest_detail': 'Detail Orientation',
        'interest_leading': 'Leadership', 
        'interest_helping': 'Helping Others', 
        'interest_tools': 'Tools/Mechanical', 
        'interest_analysis': 'Analysis',
        'interest_writing': 'Writing/Journalism', 
        'interest_performing': 'General Performing Arts', 
        'interest_health_care': 'Health Care', 
        'interest_finance': 'Finance',
        'interest_sales': 'Sales/Enterprising', 
        'interest_education': 'Teaching/Education', 
        'interest_management': 'Management', 
        'interest_marketing': 'Marketing',
        'interest_performing_arts': 'Theatre/Vocal Performance', 
        'interest_counseling': 'Counseling', 
        'interest_social_service': 'Social Service', 
        'interest_legal': 'Legal Studies',
        'interest_business': 'General Business'
    }
    
    persona = COURSE_PERSONAS.get(course_name)
    if not persona:
        return {"strengths": [f"This course is a great fit for your overall profile in your chosen field."], "growth": [], "chart_data": None}

    strengths, growth_areas, chart_labels, user_scores, ideal_scores = [], [], [], [], []
    key_traits = persona.get('key_traits', [])

    all_profile_traits = list(persona.get('profile', {}).keys())
    chart_traits = list(set(key_traits + all_profile_traits[:5]))

    for trait in chart_traits:
        user_score = user_ratings.get(trait, 0)
        ideal_score = persona.get('profile', {}).get(trait, 3)
        trait_name = TRAIT_LABEL_MAP.get(trait) or trait.replace('_', ' ').title() 

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

@login_required(login_url='/user/login/')
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

@login_required(login_url='/user/login/')
def courses_view(request):
    all_courses = Course.objects.all().order_by('name')
    context = {'active_page': 'courses', 'courses': all_courses}
    return render(request, 'recommender/courses.html', context)

@login_required(login_url='/user/login/')
def about_view(request):
    context = {'active_page': 'about'}
    return render(request, 'recommender/about.html', context)

@login_required(login_url='/user/login/')
def assessment_view(request):
    step1_items = [
        {"name": "ability_numerical", "label": "I am confident in solving complex calculations and numerical problems.", "icon": "calculator"},
        {"name": "ability_abstract_reason", "label": "I am good at finding logical patterns in sequences of shapes or numbers.", "icon": "cpu"},
        {"name": "ability_verbal_comp", "label": "I quickly understand complex written instructions or technical documents.", "icon": "file-text"},
        {"name": "ability_clerical", "label": "I am very careful at whatever I do (Clerical Speed/Accuracy).", "icon": "check-square"},
        {"name": "ability_mech_reason", "label": "I can follow a complex diagram or instructions to build something.", "icon": "tool"},
        {"name": "ability_organization", "label": "I make plans and stick to them (Systematic/Organized).", "icon": "layers"},
        {"name": "ability_detailcheck", "label": "I am confident in finding small errors or discrepancies in a long document.", "icon": "zoom-in"},
        {"name": "ability_comprehension", "label": "I quickly grasp the main idea when reading complex academic articles.", "icon": "book-open"},
        {"name": "ability_not_impulsive", "label": "I keep trying even after I fail (Persistence).", "icon": "zap"},
        {"name": "dmgt_self_manage", "label": "I think carefully before I act (Self-Management).", "icon": "target"}
    ]

    step2_items = [
        {"name": "interest_research", "label": "I enjoy technical research, analysis, and experiments.", "icon": "search"},
        {"name": "interest_tech", "label": "I enjoy using software, coding, or managing technical systems.", "icon": "code"},
        {"name": "interest_building", "label": "I enjoy manual work like building, repairing, or assembly.", "icon": "tool"},
        {"name": "interest_nature", "label": "I enjoy working outdoors, with plants, animals, or the environment.", "icon": "feather"},
        {"name": "ability_spatial", "label": "I am confident in mentally manipulating 3D objects (Spatial Aptitude).", "icon": "maximize"},
        {"name": "interest_tools", "label": "I would enjoy installing an alarm system in a building.", "icon": "wrench"},
        {"name": "interest_analysis", "label": "I would enjoy analyzing the structure of molecules.", "icon": "cpu"},
        {"name": "interest_writing", "label": "I enjoy writing scripts, reports, or articles for a public audience.", "icon": "edit"},
        {"name": "interest_performing", "label": "I enjoy composing a song or performing on stage.", "icon": "mic"},
        {"name": "interest_health_care", "label": "I would enjoy doing laboratory tests to diagnose diseases.", "icon": "activity"},
    ]

    step3_items = [
        {"name": "interest_detail", "label": "I am good at handling complex financial records, numbers, or budgets.", "icon": "file-text"},
        {"name": "interest_leading", "label": "I enjoy managing projects, organizing people, or taking charge of events.", "icon": "users"},
        {"name": "interest_helping", "label": "I enjoy counseling, mentoring, or providing direct service to people.", "icon": "heart"},
        {"name": "ability_teamwork", "label": "I am good at collaborating effectively in diverse groups.", "icon": "users"},
        {"name": "interest_finance", "label": "I would enjoy calculating the cost of an insurance claim.", "icon": "dollar-sign"},
        {"name": "interest_sales", "label": "I would enjoy persuading others to my point of view (Enterprising).", "icon": "trending-up"},
        {"name": "interest_education", "label": "I would enjoy tutoring a child or teaching adults new skills.", "icon": "book"},
        {"name": "interest_management", "label": "I would enjoy leading a team and coordinating a business conference.", "icon": "briefcase"},
        {"name": "interest_marketing", "label": "I would enjoy planning a marketing strategy for a new company.", "icon": "compass"},
        {"name": "dmgt_resilience", "label": "I know I can get through bad times (Resilience).", "icon": "shield"}
    ]

    step4_items = [
        {"name": "ability_logic", "label": "Logical thinking and solving difficult abstract or numerical problems.", "icon": "cpu"},
        {"name": "ability_creativity", "label": "Developing original ideas, solutions, or artistic concepts.", "icon": "feather"},
        {"name": "ability_comm", "label": "Verbal and written communication (Clarity of Expression).", "icon": "message-circle"},
        {"name": "ability_practical", "label": "Applying knowledge to mechanical tasks and using hands-on skills.", "icon": "tool"},
        {"name": "interest_arts", "label": "I enjoy painting, sculpting, or drawing (Artistic expression).", "icon": "edit-3"},
        {"name": "interest_policy", "label": "I enjoy studying history, social issues, governance, or international affairs.", "icon": "flag"},
        {"name": "interest_social_service", "label": "I would enjoy helping a needy family find appropriate housing.", "icon": "home"},
        {"name": "interest_legal", "label": "I would enjoy reading legal documents and researching laws.", "icon": "gavel"},
        {"name": "dmgt_patience", "label": "I remain calm and patient when a complicated task requires many attempts.", "icon": "clock"},
        {"name": "interest_performing_arts", "label": "I would enjoy performing musical theater or acting.", "icon": "star"},
    ]
    
    step5_items = [
        {"name": "ability_problem_solve", "label": "I consider the positives and negatives of every option when I am making a decision.", "icon": "target"},
        {"name": "dmgt_integrity", "label": "I stand up for what is right, even when I am scared.", "icon": "shield"},
        {"name": "dmgt_flexibility", "label": "If someone hurts me, but they say they're sorry, I forgive them.", "icon": "shuffle"},
        {"name": "dmgt_initiative", "label": "I am a very loyal member of my group.", "icon": "award"},
        {"name": "ability_comm_written", "label": "I am good at finding the best word to complete a difficult sentence.", "icon": "edit-3"},
        {"name": "ability_negotiation", "label": "I am confident in negotiating with others to reach a deal.", "icon": "gavel"},
        {"name": "interest_business", "label": "I often think about starting my own small business or company.", "icon": "briefcase"},
        {"name": "interest_science", "label": "I enjoy reading about chemistry, physics, or biology in my free time.", "icon": "activity"},
        {"name": "interest_teaching", "label": "I am good at explaining complicated concepts to others.", "icon": "book"},
        {"name": "interest_sports", "label": "I enjoy participating in competitive sports or fitness activities.", "icon": "zap"},
    ]
    
    context = {
        'active_page': 'assessment',
        'step1_items': step1_items,
        'step2_items': step2_items,
        'step3_items': step3_items,
        'step4_items': step4_items,
        'step5_items': step5_items,
    }
    return render(request, 'recommender/assessment.html', context)


@login_required(login_url='/user/login/')
def user_history_view(request):

    try:
        user_profile = request.user.userprofile
        
        assessments_list = Assessment.objects.filter(user=request.user).order_by('-timestamp')

    except UserProfile.DoesNotExist:
        messages.error(request, "Your user account is missing required profile data. Please contact support or update your profile.")
        assessments_list = Assessment.objects.none() 

    context = {
        'active_page': 'user_history',
        'assessments': assessments_list,
    }
    return render(request, 'recommender/user_history.html', context)


@login_required(login_url='/user/login/')
def user_assessment_detail_view(request, assessment_id):
    
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    if assessment.user != request.user:
        raise Http404("Assessment not found or unauthorized access.")

    formatted_answers = []
    
    for trait, question_text in ASSESSMENT_QUESTION_MAP.items():


        score = getattr(assessment, trait, None) 
        
        if score is not None:
            formatted_answers.append({
                'question': question_text, 
                'score': score
            })
    
    # Sort the answers alphabetically by question for a cleaner look
    formatted_answers.sort(key=lambda x: x['question'])

    context = {
        'assessment': assessment,
        'formatted_answers': formatted_answers,
        'active_page': 'user_history',
    }
    return render(request, 'recommender/user_assessment_detail.html', context)

@login_required(login_url='/user/login/')
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

@login_required(login_url='/user/login/')
def recommendation_view(request, assessment_id=None):
    
    import pandas as pd
    import joblib 
    
    if request.method == 'POST':
        try:
            global FIELD_MODEL, ENCODERS, MASTER_TRAIT_LIST
            if FIELD_MODEL is None or ENCODERS is None:
                field_model = joblib.load(FIELD_MODEL_PATH)
                encoders = joblib.load(ENCODERS_PATH)
            else:
                field_model = FIELD_MODEL
                encoders = ENCODERS
            
            form_data = request.POST
            try:
                profile = request.user.userprofile 
                
                assessment_kwargs = {
                    'user': request.user, 
                    'display_name': profile.name, 
                    'school': profile.university, 
                    'shs_strand': profile.strand,
                    'tvl_strand': form_data.get('tvl_strand') if profile.strand == 'TVL' else None, 
                    'last_completed_step': 5, 
                }
            except Exception as profile_e:
                print(f"CRITICAL ERROR: Failed to access user profile for assessment save: {profile_e}")
                messages.error(request, "Profile corrupted. Please log in again to register correctly.")
                auth_logout(request)
                return redirect('user_login') 
        
            for field_name in MASTER_TRAIT_LIST:
                assessment_kwargs[field_name] = int(form_data.get(field_name, 0))

            new_assessment = Assessment.objects.create(**assessment_kwargs)
            
            # --- Prediction Logic ---
            data_for_prediction = {feature: form_data.get(feature, 0) for feature in field_model.feature_names_in_}
            if 'tvl_strand' not in form_data or not data_for_prediction.get('tvl_strand'): 
                 data_for_prediction['tvl_strand'] = 'none'

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
            
            # --- Weighted Scoring ---
            recommendations, user_ratings = [], {k: int(v) for k, v in form_data.items() if k in MASTER_TRAIT_LIST}
            all_qualifying_courses = Course.objects.filter(field_category__in=top_3_field_codes).prefetch_related('offering_universities')
            course_scores = {}
            temp_persona_data = COURSE_PERSONAS 

            for course_obj in all_qualifying_courses:
                course_name = course_obj.name
                persona = temp_persona_data.get(course_name)
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
            base_score = 80
            for i, (course, data) in enumerate(top_3_ranked_courses):
                course_obj = data['object']
                uni_list = []
                for uni in course_obj.offering_universities.all():
                    clean_name = uni.name.replace('(', '').replace(')', '').strip()
                    uni_slug = clean_name.replace(' ', '-').lower()
                    uni_list.append({'name': uni.name, 'slug': uni_slug})
                
                top_score = top_3_ranked_courses[0][1]['score'] if top_3_ranked_courses else 0
                score_difference = (top_score - data['score']) if top_score > 0 else 0
                scaled_percentage = max(base_score, 98 - (i * 5) - (score_difference // 5)) 
                insights = get_in_depth_insights(course, user_ratings)

                recommendations.append({
                    'course': course, 'match_score': f"{scaled_percentage}%", 
                    'insights': insights, 'universities': uni_list 
                })
            
            new_assessment.recommended_course_1 = recommendations[0]['course'] if recommendations else ''
            new_assessment.recommended_course_2 = recommendations[1]['course'] if len(recommendations) > 1 else ''
            new_assessment.recommended_course_3 = recommendations[2]['course'] if len(recommendations) > 2 else ''
            new_assessment.save()
            
            return redirect('recommendation_result_with_id', assessment_id=new_assessment.id)
            
        except Exception as e:
            error_msg = f"Recommendation System Error: {e}. Check ML models and database setup."
            print(f"ERROR: {error_msg}")
            return render(request, 'recommender/error.html', {'error_message': error_msg})
    
    if assessment_id is not None:
        try:
            assessment = get_object_or_404(Assessment, id=assessment_id)
            recommendations = get_recommendations_from_assessment(assessment) 
            context = {'recommendations': recommendations, 'assessment_id': assessment.id,'hide_messages': True,}
            return render(request, 'recommender/recommendation_result.html', context)
            
        except Http404:
            messages.error(request, "Assessment ID not found.")
            return redirect('assessment')
        except Exception as e:
            print(f"\n--- CRASH DURING RESULTS GET REQUEST ---")
            print(f"Exception: {type(e).__name__}: {e}")
            print("-------------------------------------------\n")
            messages.error(request, f"Error loading results: {e}")
            return redirect('dashboard') 
            
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
    import csv 
    
    assessments_with_feedback = Assessment.objects.filter(feedback_submitted=True)
    new_training_data = []
    
    global MASTER_TRAIT_LIST 
    
    course_field_map = {c.name: c.field_category for c in Course.objects.all()}

    for assessment in assessments_with_feedback:
        base_data = {'shs_strand': assessment.shs_strand, 'tvl_strand': assessment.tvl_strand}
        
        for field in MASTER_TRAIT_LIST:
            base_data[field] = getattr(assessment, field, 0) 
        
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

SENDER_EMAIL = settings.ADMIN_EMAIL

def admin_login_view(request):
    if request.user.is_authenticated: return redirect('admin_dashboard')
    
    if request.method == 'POST' and '2fa_code' in request.POST:
        user_id = request.session.get('2fa_user_id')
        if not user_id: messages.error(request, 'Your session has expired.'); return redirect('login')
        
        expiry_time_str = request.session.get('2fa_expiry')
        if datetime.now().isoformat() > expiry_time_str:
            messages.error(request, 'The verification code has expired.')
            del request.session['2fa_user_id'], request.session['2fa_code'], request.session['2fa_expiry']
            return redirect('login')
            
        if str(request.POST.get('2fa_code')) == request.session.get('2fa_code'):
            try: user = User.objects.get(pk=user_id)
            except User.DoesNotExist: user = None
            if user:
                login(request, user)
                del request.session['2fa_user_id'], request.session['2fa_code'], request.session['2fa_expiry']
                
                try: 
                    send_mail('AlignEd Admin Panel: Successful Login', 
                              f"The user '{user.username}' successfully logged in.", 
                              SENDER_EMAIL, 
                              [SENDER_EMAIL]) 
                except Exception as e: print(f"Error sending login email: {e}")
                
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid verification code.')
            return render(request, 'recommender/login.html', {'awaiting_2fa': True})
            
    if request.method == 'POST' and 'username' in request.POST:
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None and user.is_superuser:
            grace_period_key = f'grace_period_user_{user.id}'
            if cache.get(grace_period_key): 
                login(request, user)
                cache.delete(grace_period_key)
                return redirect('admin_dashboard') 
                
            code, expiry_time = str(random.randint(10000, 99999)), datetime.now() + timedelta(minutes=3)
            request.session['2fa_user_id'], request.session['2fa_code'], request.session['2fa_expiry'] = user.id, code, expiry_time.isoformat()
            
            try:
                send_mail('Your AlignEd Admin Login Code', 
                          f'Your verification code is: {code}', 
                          SENDER_EMAIL, 
                          [SENDER_EMAIL])
                messages.success(request, 'A verification code has been sent to your email.')
            except Exception as e: 
                messages.error(request, 'Failed to send email.')
                print(f"Error sending 2FA email: {e}")
            
            return render(request, 'recommender/login.html', {'awaiting_2fa': True})
        else: messages.error(request, 'Invalid credentials or not an admin account.')
        
    if '2fa_user_id' in request.session: del request.session['2fa_user_id']
    return render(request, 'recommender/login.html', {'awaiting_2fa': False})

def admin_logout_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        logout(request)
        cache.set(f'grace_period_user_{user_id}', True, timeout=45)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('dashboard')

def admin_logout_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        logout(request)
        cache.set(f'grace_period_user_{user_id}', True, timeout=45)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('dashboard')
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user) 
            messages.success(request, f'Account created for {user.username}!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserRegisterForm()
        
    context = {'form': form}
    return render(request, 'recommender/register.html', context)


def user_login_view(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard') 
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    context = {'form': form}
    return render(request, 'recommender/user_login.html', context)


def user_logout_view(request):
    if request.user.is_authenticated:
        auth_logout(request)
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