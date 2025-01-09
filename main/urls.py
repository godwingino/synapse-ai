from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('pdf/<int:pk>/', views.pdf_detail, name='pdf_detail'),
    path('api/chat', views.chat_api, name='chat_api'),
]
