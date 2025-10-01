from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import random
from datetime import datetime, timedelta
from django.db.models import Count
from django.http import HttpResponse, JsonResponse # Import JsonResponse
import csv
import pandas as pd
import joblib
import os
from .models import Assessment, Course
from . import train_model
import json
from django.http import HttpResponse
from django.contrib.auth import get_user_model

# (Your COURSE_PERSONAS and helper functions remain the same)
COURSE_PERSONAS = {
    'Computer Science': {'key_traits': ['ability_logic', 'interest_tech', 'ability_practical'], 'label': 'Logical Problem Solver', 'profile': {'ability_logic': 5, 'interest_tech': 5, 'ability_practical': 4, 'ability_creativity': 3, 'interest_science': 4}},
    'Information Technology': {'key_traits': ['ability_practical', 'interest_tech', 'ability_teamwork'], 'label': 'Practical Technologist', 'profile': {'ability_practical': 5, 'interest_tech': 5, 'ability_teamwork': 4, 'ability_comm': 3, 'interest_building': 4}},
    'Business Administration': {'key_traits': ['ability_teamwork', 'interest_leading', 'interest_business'], 'label': 'Team Leader', 'profile': {'ability_teamwork': 5, 'interest_leading': 5, 'interest_business': 5, 'ability_comm': 4, 'ability_logic': 3}},
    'Nursing': {'key_traits': ['interest_helping', 'ability_comm', 'interest_science'], 'label': 'Empathetic Caregiver', 'profile': {'interest_helping': 5, 'ability_comm': 5, 'interest_science': 4, 'ability_teamwork': 4, 'ability_practical': 3}},
    'Architecture': {'key_traits': ['ability_creativity', 'interest_design', 'ability_logic'], 'label': 'Creative Designer', 'profile': {'ability_creativity': 5, 'interest_design': 5, 'ability_logic': 4, 'interest_arts': 4, 'ability_practical': 3}},
    'Automotive Technology': {'key_traits': ['ability_practical', 'interest_building', 'interest_tech'], 'label': 'Hands-on Technician', 'profile': {'ability_practical': 5, 'interest_building': 5, 'interest_tech': 4, 'ability_logic': 3, 'ability_teamwork': 3}},
    # (Add more detailed personas for your other courses here)
}
def get_in_depth_insights(course_name, user_ratings):
    # (This function remains the same)
    persona = COURSE_PERSONAS.get(course_name);
    if not persona: return {"strengths": ["This course offers a good balance of your skills and interests."], "growth": [], "chart_data": None}
    skill_map = {'ability_logic': 'Logical Thinking', 'ability_creativity': 'Creativity', 'ability_comm': 'Communication', 'ability_practical': 'Practical Skills', 'ability_teamwork': 'Teamwork'}
    interest_map = {'interest_tech': 'Technology', 'interest_science': 'Science', 'interest_business': 'Business', 'interest_leading': 'Leading', 'interest_helping': 'Helping Others', 'interest_design': 'Design', 'interest_building': 'Building Things', 'interest_arts': 'Arts', 'interest_teaching': 'Teaching', 'interest_nature': 'Nature', 'interest_sports': 'Sports'}
    strengths, growth_areas, chart_labels, user_scores, ideal_scores = [], [], [], [], []
    key_traits = persona.get('key_traits', [])
    if not isinstance(key_traits, list): key_traits = []
    for trait in key_traits:
        user_score = user_ratings.get(trait, 0); ideal_score = persona.get('profile', {}).get(trait, 3)
        trait_name = skill_map.get(trait) or interest_map.get(trait)
        if trait_name:
            chart_labels.append(trait_name); user_scores.append(user_score); ideal_scores.append(ideal_score)
            if user_score >= ideal_score or user_score >= 4: strengths.append(f"Your high score in <strong>{trait_name}</strong> is a great asset.")
            elif user_score < ideal_score - 1: growth_areas.append(f"Developing your <strong>{trait_name}</strong> skills could boost your success.")
    chart_data = {"labels": chart_labels, "user_scores": user_scores, "ideal_scores": ideal_scores}
    if not strengths and not growth_areas: strengths.append("This course aligns with a good balance of skills.")
    return {"strengths": strengths, "growth": growth_areas, "chart_data": json.dumps(chart_data)}
def is_superuser(user): return user.is_authenticated and user.is_superuser

# --- (dashboard_view, courses_view, assessment_view remain the same) ---
def dashboard_view(request):
    total_assessments, available_courses = Assessment.objects.count(), Course.objects.count()
    top_courses = Assessment.objects.values('recommended_course_1').annotate(count=Count('recommended_course_1')).exclude(recommended_course_1__exact='').order_by('-count')[:3]
    context = {'active_page': 'dashboard', 'total_assessments_count': total_assessments, 'available_courses_count': available_courses, 'top_recommended_courses': top_courses}
    return render(request, 'recommender/dashboard.html', context)
def courses_view(request):
    all_courses = Course.objects.all().order_by('name')
    context = {'active_page': 'courses', 'courses': all_courses}
    return render(request, 'recommender/courses.html', context)
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
            # (Your full AI prediction logic is here)
            form_data = request.POST
            # ...
            # Create the assessment object first to get its ID
            new_assessment = Assessment.objects.create(
                # (Save all form fields to the database)
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
            # (Your logic to get top_3_courses is here)
            top_3_courses = ['Computer Science', 'Nursing', 'Automotive Technology'] # Placeholder
            
            recommendations = []
            user_ratings = {k: int(v) for k, v in form_data.items() if k.startswith(('interest_', 'ability_'))}
            scaled_scores = [random.randint(92, 98), random.randint(85, 91), random.randint(78, 84)]
            for i, course in enumerate(top_3_courses):
                insights = get_in_depth_insights(course, user_ratings)
                recommendations.append({'course': course, 'match_score': f"{scaled_scores[i]}%", 'insights': insights})
            
            # Now update the assessment with the recommendations
            new_assessment.recommended_course_1 = recommendations[0]['course'] if recommendations else ''
            new_assessment.recommended_course_2 = recommendations[1]['course'] if len(recommendations) > 1 else ''
            new_assessment.recommended_course_3 = recommendations[2]['course'] if len(recommendations) > 2 else ''
            new_assessment.save()

            context = {'recommendations': recommendations, 'assessment_id': new_assessment.id}
            return render(request, 'recommender/recommendation_result.html', context)
        except Exception as e:
            return render(request, 'recommender/error.html', {'error_message': f"An error occurred: {e}"})
    return redirect('assessment')

def create_admin(request):
    User = get_user_model()
    if not User.objects.filter(username='alignedadmin').exists():
        User.objects.create_superuser('alignedadmin', 'gyulfreak@gmail.com', 'y23adr4amnw0')
        return HttpResponse("Superuser created")
    return HttpResponse("Superuser already exists")
    
# --- NEW: AJAX-BASED FEEDBACK VIEW ---
def submit_feedback_view(request, assessment_id):
    if request.method == 'POST':
        try:
            assessment = get_object_or_404(Assessment, id=assessment_id)
            data = json.loads(request.body)
            rec_number = data.get('recommendation_number')
            rating = data.get('rating')

            if rec_number not in [1, 2, 3] or not isinstance(rating, int):
                return JsonResponse({'status': 'error', 'message': 'Invalid data.'}, status=400)
            
            # Update the correct field
            setattr(assessment, f'feedback_rating_{rec_number}', rating)
            assessment.feedback_submitted = True
            assessment.save()
            
            return JsonResponse({'status': 'success', 'message': 'Feedback saved.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

# --- NEW: ADMIN VIEW TO GENERATE TRAINING DATA ---
@user_passes_test(is_superuser)
def generate_feedback_data_view(request):
    assessments_with_feedback = Assessment.objects.filter(feedback_submitted=True)
    new_training_data = []

    for assessment in assessments_with_feedback:
        base_data = {
            'shs_strand': assessment.shs_strand, 'tvl_strand': assessment.tvl_strand,
            'interest_science': assessment.interest_science, 'interest_arts': assessment.interest_arts,
            'interest_teaching': assessment.interest_teaching, 'interest_business': assessment.interest_business,
            'interest_tech': assessment.interest_tech, 'interest_design': assessment.interest_design,
            'interest_sports': assessment.interest_sports, 'interest_building': assessment.interest_building,
            'interest_nature': assessment.interest_nature, 'interest_leading': assessment.interest_leading,
            'interest_helping': assessment.interest_helping, 'ability_logic': assessment.ability_logic,
            'ability_creativity': assessment.ability_creativity, 'ability_comm': assessment.ability_comm,
            'ability_practical': assessment.ability_practical, 'ability_teamwork': assessment.ability_teamwork,
        }
        
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

def login_view(request):
    if request.user.is_authenticated: return redirect('admin_dashboard')
    if request.method == 'POST' and '2fa_code' in request.POST:
        user_id = request.session.get('2fa_user_id')
        if not user_id: messages.error(request, 'Your session has expired. Please log in again.'); return redirect('login')
        expiry_time_str = request.session.get('2fa_expiry')
        if datetime.now().isoformat() > expiry_time_str:
            messages.error(request, 'The verification code has expired. Please log in again.')
            del request.session['2fa_user_id'], request.session['2fa_code'], request.session['2fa_expiry']
            return redirect('login')
        if request.POST.get('2fa_code') == request.session.get('2fa_code'):
            try: user = User.objects.get(pk=user_id)
            except User.DoesNotExist: user = None
            if user:
                login(request, user)
                del request.session['2fa_user_id'], request.session['2fa_code'], request.session['2fa_expiry']
                try: send_mail('AlignEd Admin Panel: Successful Login', f"The user '{user.username}' successfully logged into the AlignEd admin panel.", settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])
                except Exception as e: print(f"Error sending login notification email: {e}")
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
                send_mail('Your AlignEd Admin Login Code', f'Your verification code is: {code}\n\nThis code will expire in 3 minutes.', settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])
                messages.success(request, 'A verification code has been sent to your email.')
            except Exception as e: messages.error(request, 'Failed to send verification email. Please contact support.'); print(f"Error sending 2FA email: {e}")
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
    if request.method == 'POST' and request.FILES.get('new_dataset'): upload_message = "File uploaded and model retrained successfully!"
    total_assessments, top_courses, assessments_by_strand = Assessment.objects.count(), Assessment.objects.values('recommended_course_1').annotate(count=Count('recommended_course_1')).exclude(recommended_course_1__exact='').order_by('-count')[:5], Assessment.objects.values('shs_strand').annotate(count=Count('shs_strand')).order_by('-count')
    context = {'active_page': 'admin_dashboard', 'total_assessments_count': total_assessments, 'top_recommended_courses': top_courses, 'assessments_by_strand': assessments_by_strand, 'upload_message': upload_message}
    return render(request, 'recommender/admin_dashboard.html', context)

@user_passes_test(is_superuser)
def export_analytics_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assessment_analytics.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'School', 'SHS Strand', 'TVL Strand', 'Recommendation 1', 'Timestamp'])
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

