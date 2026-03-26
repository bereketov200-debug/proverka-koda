from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Assignment, Submission, PeerReview
import random

@login_required
def assignment_list(request):
    assignments = Assignment.objects.filter(status='OPEN')
    return render(request, 'polls/assignment_list.html', {
        'assignments': assignments
    })

@login_required
def create_submission(request):
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment')
        code = request.POST.get('code')

        assignment = Assignment.objects.get(id=assignment_id)

        Submission.objects.create(
            assignment=assignment,
            author=request.user,
            code_content=code
        )
        return redirect('assignment_list')

    assignments = Assignment.objects.all()
    return render(request, 'polls/create_submission.html', {
        'assignments': assignments
    })

@login_required
def assign_reviews(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    submissions = list(Submission.objects.filter(assignment=assignment))
    users = list(set([s.author for s in submissions]))
    N = assignment.required_reviews_per_student

    for user in users:
        other_submissions = [s for s in submissions if s.author != user]
        selected = random.sample(other_submissions, min(N, len(other_submissions)))
        for sub in selected:
            PeerReview.objects.get_or_create(submission=sub, reviewer=user)

    # После назначения сразу показываем свои проверки
    return redirect('my_reviews')

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

    reviews = PeerReview.objects.filter(reviewer=request.user)
    return render(request, 'polls/my_reviews.html', {'reviews': reviews})