from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import Assignment, Submission, PeerReview
from django import forms
import random
from django.utils import timezone
from collections import defaultdict


def is_instructor(user):
    return user.groups.filter(name='Instructor').exists()


class StudentLoginView(LoginView):
    template_name = 'polls/registration/login_student.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('student_dashboard')


class TeacherLoginView(LoginView):
    template_name = 'polls/registration/login_teacher.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('teacher_dashboard')


def register_student(request):
    from django.contrib.auth.forms import UserCreationForm
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            student_group = Group.objects.get(name='Student')
            user.groups.add(student_group)
            messages.success(request, 'Регистрация студента успешно завершена!')
            return redirect('login_student')
    else:
        form = UserCreationForm()
    
    return render(request, 'polls/registration/register_student.html', {
        'form': form,
        'title': 'Регистрация студента'
    })


def register_teacher(request):
    from django.contrib.auth.forms import UserCreationForm
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            teacher_group = Group.objects.get(name='Instructor')
            user.groups.add(teacher_group)
            messages.success(request, 'Регистрация преподавателя успешно завершена!')
            return redirect('login_teacher')
    else:
        form = UserCreationForm()
    
    return render(request, 'polls/registration/register_teacher.html', {
        'form': form,
        'title': 'Регистрация преподавателя'
    })


@login_required
def student_dashboard(request):
    assignments = Assignment.objects.filter(status='OPEN')
    return render(request, 'polls/dashboard/student_dashboard.html', {
        'assignments': assignments
    })


@login_required
@user_passes_test(is_instructor, login_url='login_teacher')
def teacher_dashboard(request):
    assignments = Assignment.objects.filter(created_by=request.user)
    return render(request, 'polls/dashboard/teacher_dashboard.html', {
        'assignments': assignments
    })


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'submission_deadline', 'review_deadline', 'required_reviews_per_student']
        widgets = {
            'submission_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'review_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


@login_required
@user_passes_test(is_instructor, login_url='login_teacher')
def create_assignment(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, 'Задание успешно создано!')
            return redirect('teacher_dashboard')
    else:
        form = AssignmentForm()
    
    return render(request, 'polls/create_assignment.html', {'form': form})


@login_required
def assignment_list(request):
    assignments = Assignment.objects.filter(status='OPEN')
    return render(request, 'polls/assignment_list.html', {'assignments': assignments})


@login_required
def create_submission(request):
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment')
        code = request.POST.get('code')

        assignment = get_object_or_404(Assignment, id=assignment_id)

        if timezone.now() > assignment.submission_deadline:
            messages.error(request, 'Дедлайн сдачи истёк!')
            return redirect('student_dashboard')

        if Submission.objects.filter(assignment=assignment, author=request.user).exists():
            messages.error(request, 'Вы уже сдали работу по этому заданию!')
            return redirect('assignment_list')

        Submission.objects.create(
            assignment=assignment,
            author=request.user,
            code_content=code
        )
        messages.success(request, 'Работа успешно сдана!')
        return redirect('student_dashboard')

    assignments = Assignment.objects.filter(status='OPEN')
    return render(request, 'polls/create_submission.html', {'assignments': assignments})


@login_required
@user_passes_test(is_instructor, login_url='login_teacher')
def assign_reviews(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if assignment.status != 'OPEN':
        messages.error(request, 'Задание уже не в открытом статусе!')
        return redirect('teacher_dashboard')

    submissions = list(Submission.objects.filter(assignment=assignment))
    
    if len(submissions) < 2:
        messages.error(request, f'Недостаточно сданных работ. Сейчас сдано: {len(submissions)}. Нужно минимум 2 работы.')
        return redirect('teacher_dashboard')

    users = list(set([s.author for s in submissions]))
    N = assignment.required_reviews_per_student

    PeerReview.objects.filter(submission__assignment=assignment).delete()

    for user in users:
        other_submissions = [s for s in submissions if s.author != user]
        selected = random.sample(other_submissions, min(N, len(other_submissions)))
        for sub in selected:
            PeerReview.objects.get_or_create(submission=sub, reviewer=user)

    assignment.status = 'REVIEWING'
    assignment.save()

    messages.success(request, f'Рецензии успешно распределены! Каждый студент должен оценить {N} работ.')
    return redirect('teacher_dashboard')


@login_required
def my_reviews(request):
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        grade = request.POST.get('grade')
        comment = request.POST.get('comment')

        review = PeerReview.objects.get(id=review_id, reviewer=request.user)
        review.suggested_grade = grade
        review.comments = comment
        review.is_completed = True
        review.save()

        messages.success(request, 'Отзыв успешно отправлен!')
        return redirect('my_reviews')

    reviews = PeerReview.objects.filter(
        reviewer=request.user,
        is_completed=False
    ).select_related('submission', 'submission__assignment')
    
    return render(request, 'polls/my_reviews.html', {'reviews': reviews})


@login_required
def my_received_reviews(request):
    my_submissions = Submission.objects.filter(author=request.user)
    reviews = PeerReview.objects.filter(
        submission__in=my_submissions,
        is_approved_by_teacher=True,
        is_discarded=False
    ).select_related('submission', 'submission__assignment')
    
    return render(request, 'polls/my_received_reviews.html', {'reviews': reviews})


@login_required
@user_passes_test(is_instructor, login_url='login_teacher')
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    submissions = Submission.objects.filter(assignment=assignment).select_related('author')

    if request.method == 'POST':
        # Модерация отзывов
        if 'review_id' in request.POST and 'action' in request.POST:
            review = get_object_or_404(PeerReview, id=request.POST['review_id'])
            action = request.POST['action']

            if action == 'approve':
                review.is_approved_by_teacher = True
                review.is_discarded = False
                messages.success(request, 'Отзыв одобрен.')
            elif action == 'discard':
                review.is_approved_by_teacher = False
                review.is_discarded = True
                messages.success(request, 'Отзыв отклонён.')

            review.save()
            return redirect('assignment_detail', assignment_id=assignment.id)

        # Сохранение итоговой оценки
        if 'submission_id' in request.POST:
            submission = get_object_or_404(Submission, id=request.POST['submission_id'])
            final_grade = request.POST.get('final_grade')
            teacher_feedback = request.POST.get('teacher_feedback', '')

            if final_grade:
                try:
                    submission.final_grade = float(final_grade)
                except ValueError:
                    pass
            submission.teacher_feedback = teacher_feedback
            submission.save()
            messages.success(request, 'Итоговая оценка сохранена.')
            return redirect('assignment_detail', assignment_id=assignment.id)

    return render(request, 'polls/assignment_detail.html', {
        'assignment': assignment,
        'submissions': submissions
    })


@login_required
@user_passes_test(is_instructor, login_url='login_teacher')
def gradebook(request):
    assignments = Assignment.objects.filter(created_by=request.user)

    submissions = Submission.objects.filter(
        assignment__created_by=request.user
    ).select_related('author', 'assignment').order_by('author__username', 'assignment__title')

    student_grades = defaultdict(list)

    for sub in submissions:
        student_grades[sub.author].append({
            'assignment': sub.assignment,
            'final_grade': sub.final_grade,
            'teacher_feedback': sub.teacher_feedback,
            'submitted_at': sub.submitted_at
        })

    context = {
        'student_grades': dict(student_grades),
        'assignments': assignments,
    }
    
    return render(request, 'polls/gradebook.html', context)


@login_required
def home_redirect(request):
    if request.user.groups.filter(name='Instructor').exists():
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')
    
@login_required
def my_submissions(request):
    submissions = Submission.objects.filter(author=request.user).select_related('assignment')
    return render(request, 'polls/my_submissions.html', {
        'submissions': submissions
    })

@login_required
def my_grades(request):
    submissions = Submission.objects.filter(author=request.user).select_related('assignment')
    return render(request, 'polls/my_grades.html', {
        'submissions': submissions
    })