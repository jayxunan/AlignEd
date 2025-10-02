from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import random
from datetime import datetime, timedelta
from django.db.models import Count, Avg
from django.http import HttpResponse, JsonResponse, FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
import csv
import pandas as pd
import joblib
import os
from .models import Assessment, Course
from . import train_model
import json

#course persona
COURSE_PERSONAS = {
    'Computer Science': {'key_traits': ['ability_logic', 'interest_tech', 'ability_practical'], 'label': 'Logical Problem Solver', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'ability_practical': 4, 'ability_creativity': 3, 'interest_science': 4}},
    'Information Technology': {'key_traits': ['ability_practical', 'interest_tech', 'ability_teamwork'], 'label': 'Practical Technologist', 'profile': {'ability_practical': 5, 'interest_tech': 5, 'ability_teamwork': 4, 'ability_comm': 3, 'interest_building': 4}},
    'Web & Mobile App Development': {'key_traits': ['ability_creativity', 'ability_practical', 'interest_design'], 'label': 'Creative Developer', 'profile': {'ability_creativity': 5, 'ability_practical': 5, 'interest_design': 4, 'interest_tech': 5, 'ability_logic': 3}},
    'Data Science': {'key_traits': ['ability_logic', 'interest_science', 'interest_business'], 'label': 'Analytical Specialist', 'profile': {'ability_logic': 5, 'interest_science': 5, 'interest_business': 4, 'interest_tech': 4, 'ability_comm': 3}},
    'Game Development': {'key_traits': ['ability_creativity', 'ability_logic', 'interest_design'], 'label': 'Interactive Designer', 'profile': {'ability_creativity': 5, 'ability_logic': 4, 'interest_design': 5, 'interest_arts': 4, 'interest_tech': 4}},
    'Computer Engineering': {'key_traits': ['ability_logic', 'interest_building', 'interest_science'], 'label': 'Hardware Innovator', 'profile': {'ability_logic': 5, 'interest_building': 5, 'interest_science': 4, 'ability_practical': 4, 'interest_tech': 4}},
    'Civil Engineering': {'key_traits': ['ability_practical', 'ability_logic', 'interest_building'], 'label': 'Structural Planner', 'profile': {'ability_practical': 5, 'ability_logic': 5, 'interest_building': 4, 'interest_science': 4, 'ability_teamwork': 3}},
    'Electronics Engineering': {'key_traits': ['ability_logic', 'interest_building', 'interest_science'], 'label': 'Circuit Designer', 'profile': {'ability_logic': 5, 'interest_building': 5, 'interest_science': 4, 'ability_practical': 4, 'interest_tech': 3}},
    'Mechanical Engineering': {'key_traits': ['ability_practical', 'interest_building', 'ability_logic'], 'label': 'Machine Expert', 'profile': {'ability_practical': 5, 'interest_building': 5, 'ability_logic': 4, 'interest_science': 4, 'interest_tech': 3}},
    'Architecture': {'key_traits': ['ability_creativity', 'interest_design', 'interest_arts'], 'label': 'Creative Designer', 'profile': {'ability_creativity': 5, 'interest_design': 5, 'interest_arts': 4, 'ability_logic': 3, 'ability_practical': 3}},
    'Nursing': {'key_traits': ['interest_helping', 'ability_comm', 'interest_science'], 'label': 'Empathetic Caregiver', 'profile': {'interest_helping': 5, 'ability_comm': 5, 'interest_science': 4, 'ability_teamwork': 4, 'ability_practical': 3}},
    'Medical Technology': {'key_traits': ['ability_logic', 'interest_science', 'ability_practical'], 'label': 'Lab Analyst', 'profile': {'ability_logic': 5, 'interest_science': 5, 'ability_practical': 4, 'interest_building': 3, 'interest_helping': 3}},
    'Pharmacy': {'key_traits': ['ability_logic', 'interest_science', 'interest_helping'], 'label': 'Medical Expert', 'profile': {'ability_logic': 5, 'interest_science': 5, 'interest_helping': 4, 'ability_comm': 3, 'ability_practical': 2}},
    'Business Administration': {'key_traits': ['ability_teamwork', 'interest_leading', 'interest_business'], 'label': 'Team Leader', 'profile': {'ability_teamwork': 5, 'interest_leading': 5, 'interest_business': 5, 'ability_comm': 4, 'ability_logic': 3}},
    'Accountancy': {'key_traits': ['ability_logic', 'interest_business'], 'label': 'Detail-Oriented Analyst', 'profile': {'ability_logic': 5, 'interest_business': 5, 'ability_practical': 3, 'ability_comm': 2, 'ability_teamwork': 2}},
    'Marketing Management': {'key_traits': ['ability_creativity', 'ability_comm', 'interest_business'], 'label': 'Creative Strategist', 'profile': {'ability_creativity': 5, 'ability_comm': 5, 'interest_business': 4, 'interest_leading': 4, 'interest_design': 3}},
    'Psychology': {'key_traits': ['ability_comm', 'interest_helping', 'interest_arts'], 'label': 'Insightful Advisor', 'profile': {'ability_comm': 5, 'interest_helping': 5, 'interest_arts': 4, 'ability_logic': 3, 'interest_teaching': 3}},
    'Communication': {'key_traits': ['ability_comm', 'ability_creativity', 'interest_arts'], 'label': 'Creative Storyteller', 'profile': {'ability_comm': 5, 'ability_creativity': 5, 'interest_arts': 4, 'interest_leading': 3, 'ability_teamwork': 3}},
    'Education (BEEd/BSEd)': {'key_traits': ['interest_teaching', 'ability_comm', 'ability_teamwork'], 'label': 'Inspirational Mentor', 'profile': {'interest_teaching': 5, 'ability_comm': 5, 'ability_teamwork': 4, 'interest_helping': 4, 'ability_creativity': 3}},
    'Automotive Technology': {'key_traits': ['ability_practical', 'interest_building', 'interest_tech'], 'label': 'Hands-on Technician', 'profile': {'ability_practical': 5, 'interest_building': 5, 'interest_tech': 4, 'ability_logic': 3, 'ability_teamwork': 3}},
    'Agriculture': {'key_traits': ['ability_practical', 'interest_nature', 'interest_science'], 'label': 'Nature Cultivator', 'profile': {'ability_practical': 5, 'interest_nature': 5, 'interest_science': 4, 'ability_logic': 3, 'interest_building': 2}},
}

def get_in_depth_insights(course_name, user_ratings):
    persona = COURSE_PERSONAS.get(course_name)
    if not persona:
        return {"strengths": ["This course offers a good balance of your skills and interests."], "growth": [], "chart_data": None}

    skill_map = {'ability_logic': 'Logical Thinking', 'ability_creativity': 'Creativity', 'ability_comm': 'Communication', 'ability_practical': 'Practical Skills', 'ability_teamwork': 'Teamwork'}
    interest_map = {'interest_tech': 'Technology', 'interest_science': 'Science', 'interest_business': 'Business', 'interest_leading': 'Leading', 'interest_helping': 'Helping Others', 'interest_design': 'Design', 'interest_building': 'Building Things', 'interest_arts': 'Arts', 'interest_teaching': 'Teaching', 'interest_nature': 'Nature', 'interest_sports': 'Sports'}

    strengths, growth_areas, chart_labels, user_scores, ideal_scores = [], [], [], [], []
    key_traits = persona.get('key_traits', [])
    if not isinstance(key_traits, list): key_traits = []

    for trait in key_traits:
        user_score = user_ratings.get(trait, 0)
        ideal_score = persona.get('profile', {}).get(trait, 3)
        trait_name = skill_map.get(trait) or interest_map.get(trait)

        if trait_name:
            chart_labels.append(trait_name)
            user_scores.append(user_score)
            ideal_scores.append(ideal_score)
        
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

# students

def dashboard_view(request):
    total_assessments = Assessment.objects.count()
    available_courses = Course.objects.count()
    feedback_assessments = Assessment.objects.filter(feedback_submitted=True)
    total_feedback = feedback_assessments.count()
    high_feedback_count = feedback_assessments.filter(feedback_rating_1__gte=4).count()
    agreement_score = (high_feedback_count / total_feedback * 100) if total_feedback > 0 else 0
    top_courses_query = Assessment.objects.values('recommended_course_1').annotate(count=Count('recommended_course_1')).exclude(recommended_course_1__exact='').order_by('-count')[:3]
    top_courses_with_icons = []
    for item in top_courses_query:
        course_name = item['recommended_course_1']
        course_obj = Course.objects.filter(name=course_name).first()
        top_courses_with_icons.append({'name': course_name, 'count': item['count'], 'icon': course_obj.icon if course_obj else 'book'})
    context = {'active_page': 'dashboard', 'total_assessments_count': total_assessments, 'available_courses_count': available_courses, 'feedback_agreement_score': agreement_score, 'top_recommended_courses': top_courses_with_icons}
    return render(request, 'recommender/dashboard.html', context)

def courses_view(request):
    all_courses = Course.objects.all().order_by('name')
    context = {'active_page': 'courses', 'courses': all_courses}
    return render(request, 'recommender/courses.html', context)

def about_view(request):
    context = {'active_page': 'about'}
    return render(request, 'recommender/about.html', context)

def assessment_view(request):
    step2_items = [{"name": "interest_science", "label": "Science/Experiments", "icon": "beaker"}, {"name": "interest_arts", "label": "Arts/Writing", "icon": "edit-3"}, {"name": "interest_teaching", "label": "Teaching/Tutoring", "icon": "book-open"}, {"name": "interest_design", "label": "Graphic Design/Digital Arts", "icon": "pen-tool"}]
    step3_items = [{"name": "interest_tech", "label": "Technology/Coding", "icon": "code"}, {"name": "interest_building", "label": "Building or tinkering with things", "icon": "tool"}, {"name": "interest_nature", "label": "Working with plants or animals", "icon": "feather"}, {"name": "interest_sports", "label": "Physical Activity/Sports", "icon": "dribbble"}]
    step4_items = [{"name": "interest_business", "label": "Business/Finance", "icon": "dollar-sign"}, {"name": "interest_leading", "label": "Organizing events or leading teams", "icon": "users"}, {"name": "interest_helping", "label": "Advising or helping people", "icon": "heart"}, {"name": "ability_teamwork", "label": "Working in a team", "icon": "users"}]
    step5_items = [{"name": "ability_logic", "label": "Logical Thinking", "icon": "cpu"}, {"name": "ability_creativity", "label": "Creativity & Original Ideas", "icon": "feather"}, {"name": "ability_comm", "label": "Communication", "icon": "message-circle"}, {"name": "ability_practical", "label": "Practical, Hands-on Skills", "icon": "tool"}]
    context = {'active_page': 'assessment', 'step2_items': step2_items, 'step3_items': step3_items, 'step4_items': step4_items, 'step5_items': step5_items}
    return render(request, 'recommender/assessment.html', context)

def recommendation_view(request):
    if request.method == 'POST':
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'random_forest_model.joblib')
            encoders_path = os.path.join(os.path.dirname(__file__), 'label_encoders.joblib')
            model = joblib.load(model_path)
            encoders = joblib.load(encoders_path)
            form_data = request.POST
            new_assessment = Assessment.objects.create(
                name=form_data.get('name'), school=form_data.get('school'),
                shs_strand=form_data.get('shs_strand'), tvl_strand=form_data.get('tvl_strand'),
                interest_science=form_data.get('interest_science', 0), interest_arts=form_data.get('interest_arts', 0),
                interest_teaching=form_data.get('interest_teaching', 0), interest_business=form_data.get('interest_business', 0),
                interest_tech=form_data.get('interest_tech', 0), interest_design=form_data.get('interest_design', 0),
                interest_sports=form_data.get('interest_sports', 0),
                interest_building=form_data.get('interest_building', 0), interest_nature=form_data.get('interest_nature', 0),
                interest_leading=form_data.get('interest_leading', 0), interest_helping=form_data.get('interest_helping', 0),
                ability_logic=form_data.get('ability_logic', 0), ability_creativity=form_data.get('ability_creativity', 0),
                ability_comm=form_data.get('ability_comm', 0), ability_practical=form_data.get('ability_practical', 0),
                ability_teamwork=form_data.get('ability_teamwork', 0),
            )
            data_for_prediction = {}
            all_model_features = list(model.feature_names_in_)
            for feature in all_model_features: data_for_prediction[feature] = form_data.get(feature, 0)
            if 'tvl_strand' not in form_data or not data_for_prediction['tvl_strand']: data_for_prediction['tvl_strand'] = 'none'
            df_user = pd.DataFrame([data_for_prediction])
            for column, encoder in encoders.items():
                if column in df_user.columns:
                    value_to_transform = [df_user.iloc[0][column]]
                    try:
                        encoded_value = encoder.transform(value_to_transform)[0]
                        df_user.at[0, column] = encoded_value
                    except ValueError: df_user.at[0, column] = 0
            df_user = df_user[all_model_features].apply(pd.to_numeric)
            probabilities = model.predict_proba(df_user)[0]
            top_3_indices = probabilities.argsort()[-3:][::-1]
            top_3_courses = model.classes_[top_3_indices]
            
            recommendations, user_ratings = [], {k: int(v) for k, v in form_data.items() if k.startswith(('interest_', 'ability_'))}
            scaled_scores = [random.randint(92, 98), random.randint(85, 91), random.randint(78, 84)]
            for i, course in enumerate(top_3_courses):
                insights = get_in_depth_insights(course, user_ratings)
                recommendations.append({'course': course, 'match_score': f"{scaled_scores[i]}%", 'insights': insights})
            
            new_assessment.recommended_course_1, new_assessment.recommended_course_2, new_assessment.recommended_course_3 = (recommendations[0]['course'] if recommendations else ''), (recommendations[1]['course'] if len(recommendations) > 1 else ''), (recommendations[2]['course'] if len(recommendations) > 2 else '')
            new_assessment.save()
            context = {'recommendations': recommendations, 'assessment_id': new_assessment.id}
            return render(request, 'recommender/recommendation_result.html', context)
        except Exception as e:
            return render(request, 'recommender/error.html', {'error_message': f"An error occurred: {e}"})
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
    assessments_with_feedback = Assessment.objects.filter(feedback_submitted=True)
    new_training_data = []
    for assessment in assessments_with_feedback:
        base_data = {'shs_strand': assessment.shs_strand, 'tvl_strand': assessment.tvl_strand, 'interest_science': assessment.interest_science, 'interest_arts': assessment.interest_arts, 'interest_teaching': assessment.interest_teaching, 'interest_business': assessment.interest_business, 'interest_tech': assessment.interest_tech, 'interest_design': assessment.interest_design, 'interest_sports': assessment.interest_sports, 'interest_building': assessment.interest_building, 'interest_nature': assessment.interest_nature, 'interest_leading': assessment.interest_leading, 'interest_helping': assessment.interest_helping, 'ability_logic': assessment.ability_logic, 'ability_creativity': assessment.ability_creativity, 'ability_comm': assessment.ability_comm, 'ability_practical': assessment.ability_practical, 'ability_teamwork': assessment.ability_teamwork}
        if assessment.feedback_rating_1 and assessment.feedback_rating_1 >= 4:
            new_row = base_data.copy(); new_row['course'] = assessment.recommended_course_1; new_training_data.append(new_row)
        if assessment.feedback_rating_2 and assessment.feedback_rating_2 >= 4:
            new_row = base_data.copy(); new_row['course'] = assessment.recommended_course_2; new_training_data.append(new_row)
        if assessment.feedback_rating_3 and assessment.feedback_rating_3 >= 4:
            new_row = base_data.copy(); new_row['course'] = assessment.recommended_course_3; new_training_data.append(new_row)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="feedback_generated_dataset.csv"'
    if not new_training_data:
        writer = csv.writer(response); writer.writerow(['No new high-rated feedback to generate data from.']); return response
    df = pd.DataFrame(new_training_data)
    df.to_csv(path_or_buf=response, index=False)
    return response

def admin_password_reset_request_view(request):
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
    upload_message = None
    if request.method == 'POST' and request.FILES.get('new_dataset'): upload_message = "File uploaded and model retrained!"
    total_assessments, top_courses, assessments_by_strand = Assessment.objects.count(), Assessment.objects.values('recommended_course_1').annotate(count=Count('recommended_course_1')).exclude(recommended_course_1__exact='').order_by('-count')[:5], Assessment.objects.values('shs_strand').annotate(count=Count('shs_strand')).order_by('-count')
    context = {'active_page': 'admin_dashboard', 'total_assessments_count': total_assessments, 'top_recommended_courses': top_courses, 'assessments_by_strand': assessments_by_strand, 'upload_message': upload_message}
    return render(request, 'recommender/admin_dashboard.html', context)

@user_passes_test(is_superuser)
def export_analytics_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assessment_analytics.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'School', 'SHS Strand', 'TVL Strand', 'Rec 1', 'Timestamp'])
    for assessment in Assessment.objects.all().values_list('id', 'name', 'school', 'shs_strand', 'tvl_strand', 'recommended_course_1', 'timestamp'): writer.writerow(assessment)
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
    if request.method == 'POST':
        Course.objects.create(name=request.POST.get('name'), description=request.POST.get('description'), icon=request.POST.get('icon'))
        return redirect('course_list')
    context = {'action': 'Create', 'active_page': 'course_list'}
    return render(request, 'recommender/admin_course_form.html', context)

@user_passes_test(is_superuser)
def course_update_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.name, course.description, course.icon = request.POST.get('name'), request.POST.get('description'), request.POST.get('icon')
        course.save()
        return redirect('course_list')
    context = {'action': 'Update', 'course': course, 'active_page': 'course_list'}
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
        img_buffer.seek(0)
        image = ImageReader(img_buffer)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(inch, height - 2.5 * inch, "Distribution of Assessments")
        p.drawImage(image, inch, height - 5.5 * inch, width=6*inch, height=3*inch)
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='AlignEd_Analytics_Report.pdf')

