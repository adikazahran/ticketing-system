# tickets/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'), # Halaman utama dashboard
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('ticket/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('ticket/new/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('ticket/<int:pk>/edit/', views.TicketUpdateView.as_view(), name='ticket_update'),
    path('ticket/<int:pk>/delete/', views.TicketDeleteView.as_view(), name='ticket_delete'),
    path('ticket/<int:pk>/assign-to-me/', views.assign_ticket_to_me, name='assign_ticket_to_me'),

    # URL Autentikasi
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='dashboard'), name='logout'), # Redirect ke dashboard setelah logout
]