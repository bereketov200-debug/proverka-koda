from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('register/student/', views.register_student, name='register_student'),
    path('register/teacher/', views.register_teacher, name='register_teacher'),
    
    path('login/student/', views.StudentLoginView.as_view(), name='login_student'),
    path('login/teacher/', views.TeacherLoginView.as_view(), name='login_teacher'),
    
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),

    path('assignments/', views.assignment_list, name='assignment_list'),
    path('submit/', views.create_submission, name='create_submission'),
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('my-received-reviews/', views.my_received_reviews, name='my_received_reviews'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),
    path('my-grades/', views.my_grades, name='my_grades'),
    path('assign/<int:assignment_id>/', views.assign_reviews, name='assign_reviews'),
    path('create-assignment/', views.create_assignment, name='create_assignment'),
    path('assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    
    path('', views.home_redirect, name='home'),
    path('gradebook/', views.gradebook, name='gradebook'),
    path('gradebook/', views.gradebook, name='gradebook'),
    path('my-received-reviews/', views.my_received_reviews, name='my_received_reviews'),
]