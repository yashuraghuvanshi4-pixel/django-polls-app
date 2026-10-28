import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import VoteForm
from .models import Choice, Question


def create_question(question_text, days_offset=0, is_active=True):
    """
    Helper function to create a question with the given `question_text`
    and published the given number of `days_offset` to now.
    """
    time = timezone.now() + datetime.timedelta(days=days_offset)
    return Question.objects.create(
        question_text=question_text,
        pub_date=time,
        is_active=is_active
    )


def create_choice(question, choice_text, votes=0):
    """Helper function to create a choice for a given question."""
    return Choice.objects.create(
        question=question,
        choice_text=choice_text,
        votes=votes
    )


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """was_published_recently() returns False for questions whose pub_date is in the future."""
        future_time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=future_time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """was_published_recently() returns False for questions whose pub_date is older than 1 day."""
        old_time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=old_time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """was_published_recently() returns True for questions whose pub_date is within the last day."""
        recent_time = timezone.now() - datetime.timedelta(hours=23, minutes=59)
        recent_question = Question(pub_date=recent_time)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_choice_percentage_calculation(self):
        """Choice.percentage correctly computes percentage of total votes."""
        q = create_question("Sample Question")
        c1 = create_choice(q, "Choice 1", votes=3)
        c2 = create_choice(q, "Choice 2", votes=1)
        self.assertEqual(q.total_votes(), 4)
        self.assertEqual(c1.percentage, 75.0)
        self.assertEqual(c2.percentage, 25.0)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """If no questions exist, an appropriate message is displayed."""
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls match your criteria.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question_is_displayed(self):
        """Questions with a pub_date in the past are displayed on the index page."""
        question = create_question("Past Question.", days_offset=-5)
        create_choice(question, "Option A")
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question])

    def test_future_question_is_hidden(self):
        """Questions with a pub_date in the future are not displayed on the index page."""
        create_question("Future Question.", days_offset=5)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls match your criteria.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])


class QuestionDetailViewTests(TestCase):
    def test_future_question_returns_404(self):
        """The detail view of a question with a pub_date in the future returns a 404 not found."""
        future_question = create_question("Future Question", days_offset=5)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_renders_successfully(self):
        """The detail view of a published question displays the question text and options."""
        past_question = create_question("Active Question", days_offset=-1)
        choice = create_choice(past_question, "Choice Alpha")
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, past_question.question_text)
        self.assertContains(response, choice.choice_text)


class VoteViewTests(TestCase):
    def test_voting_without_choice_selection(self):
        """Submitting a vote without choosing an option returns an error on detail page."""
        question = create_question("Which color?", days_offset=-1)
        create_choice(question, "Blue")
        url = reverse("polls:vote", args=(question.id,))
        response = self.client.post(url, {})  # empty POST data
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You didn&#x27;t select a choice")

    def test_voting_with_valid_choice(self):
        """Submitting a valid choice increments vote count and redirects to results."""
        question = create_question("Which fruit?", days_offset=-1)
        choice = create_choice(question, "Apple", votes=0)
        url = reverse("polls:vote", args=(question.id,))
        response = self.client.post(url, {"choice": choice.id})

        # Should redirect (HTTP 302) to results
        self.assertRedirects(response, reverse("polls:results", args=(question.id,)))

        # Refresh from database and assert increment
        choice.refresh_from_db()
        self.assertEqual(choice.votes, 1)

    def test_voting_on_inactive_question(self):
        """Submitting a vote on an inactive question is rejected with validation error."""
        question = create_question("Closed Poll", days_offset=-1, is_active=False)
        choice = create_choice(question, "Choice 1")
        url = reverse("polls:vote", args=(question.id,))
        response = self.client.post(url, {"choice": choice.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This poll is closed")


class PollCreateViewTests(TestCase):
    def test_get_create_poll_page(self):
        """GET /polls/create/ renders the poll creation form."""
        response = self.client.get(reverse("polls:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create a New Poll")

    def test_post_create_poll_success(self):
        """POST /polls/create/ creates Question and Choices and redirects to detail page."""
        data = {
            "question_text": "What is your favorite coffee?",
            "choice_1": "Espresso",
            "choice_2": "Cappuccino",
            "choice_3": "Cold Brew",
            "is_active": True,
        }
        response = self.client.post(reverse("polls:create"), data)
        q = Question.objects.get(question_text="What is your favorite coffee?")
        self.assertRedirects(response, reverse("polls:detail", args=(q.id,)))
        self.assertEqual(q.choices.count(), 3)


class AnalyticsDashboardViewTests(TestCase):
    def test_dashboard_renders_metrics(self):
        """GET /polls/dashboard/ displays aggregate metrics and leaderboard."""
        q = create_question("Database Survey")
        create_choice(q, "PostgreSQL", votes=10)
        create_choice(q, "MySQL", votes=5)

        response = self.client.get(reverse("polls:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Community Analytics &amp; Leaderboard")
        self.assertContains(response, "PostgreSQL")
        self.assertEqual(response.context["total_votes"], 15)

