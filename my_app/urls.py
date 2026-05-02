from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/events/', views.api_events, name='api_events'),
    path('add-reminder/', views.add_reminder, name='add_reminder'),
    path('login/', views.login_request, name='login'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('contact/', views.contact_view, name='contact'),
    path('delete-reminder/<int:task_id>/', views.delete_reminder, name='delete_reminder'),
    path('documents/', views.documents, name='documents'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('ai-assistant/', views.ai_assistant_view, name='ai_assistant'),
    path('api/ai-assistant/', views.ai_assistant_api, name='ai_assistant_api'),
    path('delete-document/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('add-to-calendar/', views.add_to_calendar, name='add_to_calendar'),
    path('search/', views.search_results, name='search_results'),

    # Add these two URL patterns for exam and scheme details
    path('exam/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('scheme/<int:scheme_id>/', views.scheme_detail, name='scheme_detail'),

    # ✅ single details page for both exams & schemes
    path('details/<str:item_type>/<int:item_id>/', views.details_view, name='details'),

    path('success/', views.registration_success, name='registration_success'),
    
]
