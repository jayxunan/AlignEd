from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.user_login_view, name='root'), 
    
    path('register/', views.register_view, name='register'),
    path('user/login/', views.user_login_view, name='user_login'),
    path('user/logout/', views.user_logout_view, name='user_logout'), 
    path('my-results/', views.user_history_view, name='user_history'),
    path('my-results/detail/<int:assessment_id>/', views.user_assessment_detail_view, name='user_assessment_detail'),

    path('admin-auth/', views.admin_login_view, name='admin_login'),
    path('admin-auth/logout/', views.admin_logout_view, name='admin_logout'),

    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('courses/', views.courses_view, name='courses'),
    path('assessment/', views.assessment_view, name='assessment'),
    path('about/', views.about_view, name='about'),
    path('settings/', views.user_settings_view, name='user_settings'),
    path('settings/confirm/', views.confirm_verification_view, name='confirm_settings'),

    # Recommendation Results and Processing
    path('recommendation/', views.recommendation_view, name='recommendation_result'),
    path('recommendation/<int:assessment_id>/', views.recommendation_view, name='recommendation_result_with_id'),

    # Feedback/Email Actions
    path('submit-feedback/<int:assessment_id>/', views.submit_feedback_view, name='submit_feedback'),
    path('email-results/<int:assessment_id>/', views.email_recommendations_view, name='email_recommendations'),
    
    # University Info Page
    path('university/<str:uni_slug>/', views.university_info_view, name='university_info'),

    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/history/', views.assessment_history_view, name='assessment_history'),
    path('admin-dashboard/generate-feedback-data/', views.generate_feedback_data_view, name='generate_feedback_data'),
    path('delete-assessments/', views.delete_all_assessments_view, name='delete_assessments'),
    
    # Export
    path('export-analytics/', views.export_analytics_view, name='export_analytics'),
    path('export-analytics/pdf/', views.export_analytics_pdf_view, name='export_analytics_pdf'),

    # Admin Course Controls
    path('admin-dashboard/courses/', views.course_list_view, name='course_list'),
    path('admin-dashboard/courses/new/', views.course_create_view, name='course_create'),
    path('admin-dashboard/courses/<int:pk>/edit/', views.course_update_view, name='course_update'),
    path('admin-dashboard/courses/<int:pk>/delete/', views.course_delete_view, name='course_delete'),

    path('user/password_reset/', auth_views.PasswordResetView.as_view(
        template_name="recommender/registration/user_password_reset_form.html",
        email_template_name="recommender/registration/user_password_reset_email.html",
        subject_template_name="recommender/registration/user_password_reset_subject.txt",
        success_url='/user/password_reset/done/'
    ), name='user_password_reset'),
    
    path('user/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name="recommender/registration/user_password_reset_done.html"
    ), name='password_reset_done'), 
    
    path('user/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="recommender/registration/user_password_reset_confirm.html",
        success_url='/user/reset/done/' 
    ), name='password_reset_confirm'), 
    
    path('user/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name="recommender/registration/user_password_reset_complete.html"
    ), name='password_reset_complete'),

    path('admin/password_reset_request/', views.admin_password_reset_request_view, name='admin_password_reset_request'),
]