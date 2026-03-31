from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    submission_deadline = models.DateTimeField()
    review_deadline = models.DateTimeField()
    required_reviews_per_student = models.IntegerField(default=3)

    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assignments_created'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('OPEN', 'Open'),
            ('REVIEWING', 'Reviewing'),
            ('CLOSED', 'Closed')
        ],
        default='OPEN'
    )

    def __str__(self):
        return self.title


class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='submissions'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE
    )
    code_content = models.TextField()
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    final_grade = models.FloatField(null=True, blank=True)
    teacher_feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ('assignment', 'author')

    def __str__(self):
        return f"{self.author.username} - {self.assignment.title}"


class PeerReview(models.Model):
    submission = models.ForeignKey(
        Submission, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_reviews'
    )

    comments = models.TextField(blank=True)
    suggested_grade = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )

    is_completed = models.BooleanField(default=False)
    is_approved_by_teacher = models.BooleanField(default=False)
    is_discarded = models.BooleanField(default=False)

    class Meta:
        unique_together = ('submission', 'reviewer')

    def __str__(self):
        return f"Review by {self.reviewer.username}"