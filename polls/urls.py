from django.urls import path
from . import views

urlpatterns = [
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('submit/', views.create_submission, name='create_submission'),
    path('assign/<int:assignment_id>/', views.assign_reviews, name='assign_reviews'),
    path('my_reviews/', views.my_reviews, name='my_reviews'),
]