import json
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.contrib import messages
from django.views.decorators.http import require_POST

from .forms import VoteForm, PollCreateForm
from .models import Choice, Question


def single_app_view(request):
    """
    Unified Single Web Application:
    Combines Explore, Voting, Live Results, Poll Creation, and Community Analytics
    into a single cohesive, interactive application interface.
    """
    now = timezone.now()
    questions = Question.objects.filter(pub_date__lte=now).prefetch_related("choices").order_by("-pub_date")
    
    total_questions = questions.count()
    active_questions = questions.filter(is_active=True).count()
    total_votes = Choice.objects.aggregate(total=Sum("votes"))["total"] or 0
    top_choices = Choice.objects.select_related("question").order_by("-votes")[:6]

    create_form = PollCreateForm()

    context = {
        "questions": questions,
        "latest_question_list": questions,
        "total_questions": total_questions,
        "active_questions": active_questions,
        "total_votes": total_votes,
        "top_choices": top_choices,
        "create_form": create_form,
    }
    return render(request, "polls/single_app.html", context)


# --- REST API Endpoints for Single Web Application Interactions ---

def api_polls(request):
    """Returns all published polls as JSON for client-side interactions."""
    now = timezone.now()
    questions = Question.objects.filter(pub_date__lte=now).prefetch_related("choices").order_by("-pub_date")
    
    data = []
    for q in questions:
        data.append({
            "id": q.id,
            "question_text": q.question_text,
            "pub_date": q.pub_date.strftime("%b %d, %Y"),
            "is_active": q.is_active,
            "total_votes": q.total_votes(),
            "was_recent": q.was_published_recently(),
            "choices": [
                {
                    "id": c.id,
                    "text": c.choice_text,
                    "votes": c.votes,
                    "percentage": c.percentage
                }
                for c in q.choices.all()
            ]
        })
    return JsonResponse({"polls": data})


def api_poll_detail(request, pk):
    """Returns details and choices for a single poll as JSON."""
    q = get_object_or_404(Question, pk=pk)
    return JsonResponse({
        "id": q.id,
        "question_text": q.question_text,
        "pub_date": q.pub_date.strftime("%B %d, %Y"),
        "is_active": q.is_active,
        "total_votes": q.total_votes(),
        "choices": [
            {
                "id": c.id,
                "text": c.choice_text,
                "votes": c.votes,
                "percentage": c.percentage
            }
            for c in q.choices.all()
        ]
    })


@require_POST
def api_vote(request, pk):
    """
    API endpoint for casting a vote asynchronously in the Single Web Application.
    Uses atomic F() expressions and returns updated poll results in JSON.
    """
    question = get_object_or_404(Question, pk=pk)
    
    if not question.is_active:
        return JsonResponse({"status": "error", "message": "This poll is closed."}, status=400)

    choice_id = request.POST.get("choice")
    if not choice_id:
        return JsonResponse({"status": "error", "message": "Please select a choice before voting."}, status=400)

    try:
        choice = question.choices.get(pk=choice_id)
    except Choice.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Invalid choice selected for this poll."}, status=400)

    # Atomic DB update
    Choice.objects.filter(pk=choice.pk).update(votes=F("votes") + 1)
    
    # Reload question to compute new stats
    question.refresh_from_db()
    
    return JsonResponse({
        "status": "success",
        "message": f"Your vote for '{choice.choice_text}' has been recorded!",
        "total_votes": question.total_votes(),
        "choices": [
            {
                "id": c.id,
                "text": c.choice_text,
                "votes": c.votes,
                "percentage": c.percentage
            }
            for c in question.choices.all()
        ]
    })


@require_POST
def api_create(request):
    """
    API endpoint to create a new poll asynchronously from the Single Web Application.
    """
    form = PollCreateForm(request.POST)
    if form.is_valid():
        poll = form.save()
        return JsonResponse({
            "status": "success",
            "message": f"Poll '{poll.question_text}' created successfully!",
            "poll": {
                "id": poll.id,
                "question_text": poll.question_text,
                "pub_date": poll.pub_date.strftime("%b %d, %Y"),
                "is_active": poll.is_active,
                "total_votes": 0,
                "choices": [{"id": c.id, "text": c.choice_text, "votes": 0, "percentage": 0.0} for c in poll.choices.all()]
            }
        })
    else:
        errors = [str(err) for errs in form.errors.values() for err in errs]
        return JsonResponse({"status": "error", "message": " ".join(errors)}, status=400)


# --- Standard Multi-Page Views (Preserved for Direct Navigation / SEO / Backwards-Compatibility) ---

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"
    paginate_by = 10

    def get_queryset(self):
        qs = Question.objects.filter(pub_date__lte=timezone.now()).prefetch_related("choices").order_by("-pub_date")
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(question_text__icontains=query)
        status = self.request.GET.get("status", "").strip().lower()
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "closed":
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "all")
        context["total_polls_count"] = Question.objects.count()
        return context


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = VoteForm(question=self.object)
        return context


def vote(request, pk):
    question = get_object_or_404(Question.objects.filter(pub_date__lte=timezone.now()), pk=pk)
    if request.method != "POST":
        return redirect("polls:detail", pk=question.id)

    form = VoteForm(request.POST, question=question)
    if form.is_valid():
        selected_choice = form.cleaned_data["choice"]
        Choice.objects.filter(pk=selected_choice.pk).update(votes=F("votes") + 1)
        messages.success(request, f"Your vote for '{selected_choice.choice_text}' was successfully cast!")
        return redirect("polls:results", pk=question.id)
    else:
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "form": form,
                "error_message": form.errors.get("choice") or form.non_field_errors(),
            },
        )


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())


def poll_create(request):
    if request.method == "POST":
        form = PollCreateForm(request.POST)
        if form.is_valid():
            new_poll = form.save()
            messages.success(request, f"Poll '{new_poll.question_text}' created successfully!")
            return redirect("polls:detail", pk=new_poll.id)
    else:
        form = PollCreateForm()
    return render(request, "polls/create.html", {"form": form})


def analytics_dashboard(request):
    total_questions = Question.objects.count()
    active_questions = Question.objects.filter(is_active=True).count()
    total_votes = Choice.objects.aggregate(total=Sum("votes"))["total"] or 0
    top_choices = Choice.objects.select_related("question").order_by("-votes")[:6]
    recent_polls = Question.objects.prefetch_related("choices").order_by("-pub_date")[:5]

    context = {
        "total_questions": total_questions,
        "active_questions": active_questions,
        "total_votes": total_votes,
        "top_choices": top_choices,
        "recent_polls": recent_polls,
    }
    return render(request, "polls/dashboard.html", context)
