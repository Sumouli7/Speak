from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import LoginView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('', views.main_home, name='main_home'),

    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('user-register/', views.user_register, name='user_register_alt'),

    path('employee/login/', views.employee_login, name='employee_login'),
    path('employee/register/', views.employee_register, name='employee_register'),

    path('logout/', views.user_logout, name='logout'),

    path('user-dashboard/', views.user_home, name='user_dashboard'),
    path('counselor-dashboard/', views.counselor_home, name='counselor_dashboard'),

    path('create-slot/', views.create_slot, name='create_slot'),

    path('book/<int:slot_id>/', views.book_session, name='book_session'),

    path('payment/<int:booking_id>/', views.payment, name='payment'),
    path('payment-success/<int:booking_id>/', views.payment_success, name='payment_success'),

    


    path('session/<int:booking_id>/', views.session_room, name='session_room'),
    path('submit-rating/<int:booking_id>/', views.submit_rating, name='submit_rating'),

]
    
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)