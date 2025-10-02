from django.urls import path
from . import views

urlpatterns = [
    # adminlogin
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('submit-feedback/<int:assessment_id>/', views.submit_feedback_view, name='submit_feedback'),

    # sidbar nav
    path('', views.dashboard_view, name='dashboard'),
    path('courses/', views.courses_view, name='courses'),
    path('assessment/', views.assessment_view, name='assessment'),
    path('about/', views.about_view, name='about'),
    path('recommendation/', views.recommendation_view, name='recommendation_result'),

    # admin pages
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/generate-feedback-data/', views.generate_feedback_data_view, name='generate_feedback_data'),
    path('export-analytics/', views.export_analytics_view, name='export_analytics'),
    path('export-analytics/pdf/', views.export_analytics_pdf_view, name='export_analytics_pdf'),
    path('delete-assessments/', views.delete_all_assessments_view, name='delete_assessments'),

    # admin course controls
    path('admin-dashboard/courses/', views.course_list_view, name='course_list'),
    path('admin-dashboard/courses/new/', views.course_create_view, name='course_create'),
    path('admin-dashboard/courses/<int:pk>/edit/', views.course_update_view, name='course_update'),
    path('admin-dashboard/courses/<int:pk>/delete/', views.course_delete_view, name='course_delete'),
]

