import datetime
from django.db import models
from django.utils import timezone
from django.contrib import admin


class Question(models.Model):
    """
    Represents a poll question.
    Contains the question prompt, publication date, and active status flag.
    """
    question_text = models.CharField(
        max_length=200,
        verbose_name="Question Text",
        help_text="Enter the question or statement for users to vote on."
    )
    pub_date = models.DateTimeField(
        verbose_name="Date Published",
        default=timezone.now,
        help_text="Date and time when the poll becomes visible to users."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Designates whether this poll is currently accepting votes."
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Poll Question"
        verbose_name_plural = "Poll Questions"

    def __str__(self):
        return self.question_text

    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )
    def was_published_recently(self):
        """
        Returns True if the question was published within the past 24 hours
        and not in the future.
        """
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def total_votes(self):
        """Computes the total number of votes cast across all choices."""
        return sum(choice.votes for choice in self.choices.all())


class Choice(models.Model):
    """
    Represents an option for a given Question.
    Maintains a vote counter and relation to its parent Question.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Poll Question"
    )
    choice_text = models.CharField(
        max_length=200,
        verbose_name="Choice Text"
    )
    votes = models.PositiveIntegerField(
        default=0,
        verbose_name="Vote Count"
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Choice"
        verbose_name_plural = "Choices"

    def __str__(self):
        return self.choice_text

    @property
    def percentage(self):
        """Calculates percentage of total votes for this question."""
        total = self.question.total_votes()
        if total == 0:
            return 0.0
        return round((self.votes / total) * 100, 1)
