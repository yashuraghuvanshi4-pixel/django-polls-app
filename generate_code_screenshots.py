import os
import subprocess
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

BASE_DIR = "/Users/yashuraghuvanshi/.gemini/antigravity/scratch/django_polls"
OUTPUT_DIR = "/Users/yashuraghuvanshi/.gemini/antigravity/brain/27e872c4-0096-4ca8-b82a-bbcff022f409/screenshots"
DOCS_SCREENSHOT_DIR = os.path.join(BASE_DIR, "docs/screenshots")
HTML_DIR = os.path.join(BASE_DIR, "docs/code_html")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_SCREENSHOT_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

formatter = HtmlFormatter(
    style="monokai",
    linenos=True,
    cssclass="sourcecode",
    lineanchors="line",
    linespans="line",
)
css_styles = formatter.get_style_defs(".sourcecode")

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    background-color: #0b0f19;
    margin: 0;
    padding: 30px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
  }}
  .window {{
    background: #181c24;
    border-radius: 12px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.75);
    border: 1px solid #2a303c;
    overflow: hidden;
    width: 1100px;
    max-width: 1100px;
  }}
  .titlebar {{
    background: #202632;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid #2a303c;
  }}
  .traffic-lights {{
    display: flex;
    gap: 8px;
    margin-right: 18px;
  }}
  .dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }}
  .dot-red {{ background: #ff5f56; }}
  .dot-yellow {{ background: #ffbd2e; }}
  .dot-green {{ background: #27c93f; }}
  .filename {{
    color: #e2e8f0;
    font-size: 13.5px;
    font-family: "SF Mono", Menlo, Consolas, Monaco, monospace;
    font-weight: 600;
  }}
  .badge {{
    margin-left: auto;
    background: #4f46e5;
    color: white;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }}
  .editor {{
    padding: 22px 24px;
    font-family: "SF Mono", Menlo, Consolas, Monaco, monospace;
    font-size: 13.5px;
    line-height: 1.6;
    overflow-x: auto;
  }}
  table.sourcetable {{
    border-collapse: collapse;
    width: 100%;
  }}
  td.linenos {{
    color: #4b5563;
    text-align: right;
    padding-right: 20px;
    user-select: none;
    border-right: 1px solid #2a303c;
    width: 42px;
  }}
  td.code {{
    padding-left: 20px;
  }}
  pre {{
    margin: 0;
  }}
  {css}
</style>
</head>
<body>
  <div class="window">
    <div class="titlebar">
      <div class="traffic-lights">
        <div class="dot dot-red"></div>
        <div class="dot dot-yellow"></div>
        <div class="dot dot-green"></div>
      </div>
      <div class="filename">{filename} &bull; {tagline}</div>
      <div class="badge">{badge}</div>
    </div>
    <div class="editor">
      {highlighted_code}
    </div>
  </div>
</body>
</html>
"""

# 1. Models snippet: models.py
models_code = """from django.db import models
from django.utils import timezone
from django.contrib import admin
import datetime

class Question(models.Model):
    \"\"\"Represents a poll question prompt and publishing schedule.\"\"\"
    question_text = models.CharField(max_length=200, verbose_name="Question Text")
    pub_date = models.DateTimeField(verbose_name="Date Published", default=timezone.now)
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Poll Question"

    def __str__(self):
        return self.question_text

    @admin.display(boolean=True, ordering="pub_date", description="Published recently?")
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def total_votes(self):
        \"\"\"Computes total votes across all associated choices.\"\"\"
        return sum(choice.votes for choice in self.choices.all())


class Choice(models.Model):
    \"\"\"Represents a choice option linked via ForeignKey to Question.\"\"\"
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    choice_text = models.CharField(max_length=200, verbose_name="Choice Text")
    votes = models.PositiveIntegerField(default=0, verbose_name="Vote Count")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.choice_text

    @property
    def percentage(self):
        \"\"\"Dynamic percentage calculation against total question votes.\"\"\"
        total = self.question.total_votes()
        return round((self.votes / total) * 100, 1) if total > 0 else 0.0
"""

# 2. Views snippet: views.py
views_code = """from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import VoteForm, PollCreateForm
from .models import Choice, Question

def single_app_view(request):
    \"\"\"Unified Single Web Application: renders full dashboard, search & voting.\"\"\"
    questions = Question.objects.filter(pub_date__lte=timezone.now()).prefetch_related("choices")
    return render(request, "polls/single_app.html", {
        "questions": questions,
        "total_questions": questions.count(),
        "total_votes": Choice.objects.aggregate(total=Sum("votes"))["total"] or 0,
        "top_choices": Choice.objects.select_related("question").order_by("-votes")[:6],
    })

@require_POST
def api_vote(request, pk):
    \"\"\"
    Atomic Voting Endpoint:
    Uses F('votes') + 1 database expressions to eliminate concurrency race conditions.
    \"\"\"
    question = get_object_or_404(Question, pk=pk)
    choice_id = request.POST.get("choice")
    choice = question.choices.get(pk=choice_id)

    # Atomic SQL: UPDATE polls_choice SET votes = votes + 1 WHERE id = ...
    Choice.objects.filter(pk=choice.pk).update(votes=F("votes") + 1)
    question.refresh_from_db()

    return JsonResponse({
        "status": "success",
        "message": f"Your vote for '{choice.choice_text}' was recorded!",
        "total_votes": question.total_votes(),
        "choices": [{"id": c.id, "text": c.choice_text, "votes": c.votes, "percentage": c.percentage}
                    for c in question.choices.all()]
    })
"""

# 3. Forms snippet: forms.py
forms_code = """from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Question, Choice

class VoteForm(forms.Form):
    \"\"\"
    Validates user vote submission.
    Dynamically scopes queryset to only include choices of the current question.
    \"\"\"
    choice = forms.ModelChoiceField(
        queryset=Choice.objects.none(),
        widget=forms.RadioSelect(attrs={"class": "poll-radio-input"}),
        empty_label=None,
        error_messages={"required": "Please select a choice before voting."}
    )

    def __init__(self, *args, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        if question is not None:
            # Prevents voting on choices belonging to other questions
            self.fields["choice"].queryset = question.choices.all()

class PollCreateForm(forms.Form):
    \"\"\"User-facing form allowing creation of a new poll and its choices.\"\"\"
    question_text = forms.CharField(max_length=200, label="Poll Question")
    choice_1 = forms.CharField(max_length=200, label="Option 1")
    choice_2 = forms.CharField(max_length=200, label="Option 2")
    choice_3 = forms.CharField(max_length=200, required=False, label="Option 3")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("choice_1", "").strip().lower() == cleaned.get("choice_2", "").strip().lower():
            raise ValidationError("Option 1 and Option 2 cannot be identical.")
        return cleaned

    def save(self):
        question = Question.objects.create(
            question_text=self.cleaned_data["question_text"],
            pub_date=timezone.now()
        )
        for f in ["choice_1", "choice_2", "choice_3"]:
            text = self.cleaned_data.get(f, "").strip()
            if text:
                Choice.objects.create(question=question, choice_text=text, votes=0)
        return question
"""

# 4. Admin snippet: admin.py
admin_code = """from django.contrib import admin
from .models import Question, Choice

admin.site.site_header = "PollMaster Administration"
admin.site.site_title = "PollMaster Admin Portal"

class ChoiceInline(admin.TabularInline):
    \"\"\"Enables editing choices directly within the Question detail view.\"\"\"
    model = Choice
    extra = 3
    fields = ("choice_text", "votes")

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Question Details", {"fields": ["question_text", "is_active"]}),
        ("Publication Schedule", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]
    list_display = [
        "question_text",
        "pub_date",
        "was_published_recently",
        "is_active",
        "total_votes_display"
    ]
    list_filter = ["is_active", "pub_date"]
    search_fields = ["question_text"]
    date_hierarchy = "pub_date"
    actions = ["activate_polls", "deactivate_polls", "reset_all_votes"]

    @admin.display(description="Total Votes")
    def total_votes_display(self, obj):
        return obj.total_votes()

    @admin.action(description="Reset vote counts for selected polls")
    def reset_all_votes(self, request, queryset):
        for q in queryset:
            q.choices.update(votes=0)
        self.message_user(request, "Votes successfully reset to 0.")
"""

# 5. URLs snippet: urls.py
urls_code = """# mysite/urls.py (Root Project URL Routing)
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

urlpatterns = [
    path("", lambda request: redirect("polls:index")),
    path("polls/", include("polls.urls")),
    path("admin/", admin.site.urls),
]

# polls/urls.py (App-Level Namespaced URL Routing)
from django.urls import path
from . import views

app_name = "polls"

urlpatterns = [
    # Unified Single Web Application & Dashboard
    path("", views.single_app_view, name="index"),

    # REST APIs for Dynamic Asynchronous Client Interactions
    path("api/polls/", views.api_polls, name="api_polls"),
    path("api/polls/<int:pk>/", views.api_poll_detail, name="api_poll_detail"),
    path("api/polls/<int:pk>/vote/", views.api_vote, name="api_vote"),
    path("api/polls/create/", views.api_create, name="api_create"),

    # Direct Bookmarks & Multi-Page View Access
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("create/", views.poll_create, name="create"),
]
"""

files_to_render = [
    ("backend_models.png", "polls/models.py", "Django Model Layer & ORM", "DJANGO MODEL", models_code, 1180, 890),
    ("backend_views.png", "polls/views.py", "View Logic & Atomic F() Voting", "DJANGO VIEW", views_code, 1180, 860),
    ("backend_forms.png", "polls/forms.py", "Forms Validation & Scoping", "DJANGO FORM", forms_code, 1180, 930),
    ("backend_admin.png", "polls/admin.py", "Admin Portal & Inline Customization", "DJANGO ADMIN", admin_code, 1180, 880),
    ("backend_urls.png", "polls/urls.py & mysite/urls.py", "Clean URL Routing & Namespaces", "DJANGO ROUTER", urls_code, 1180, 820),
]

for filename, filepath, tagline, badge, code, width, height in files_to_render:
    highlighted = highlight(code, PythonLexer(), formatter)
    html_content = TEMPLATE.format(
        filename=filepath,
        tagline=tagline,
        badge=badge,
        css=css_styles,
        highlighted_code=highlighted
    )
    html_file = os.path.join(HTML_DIR, f"{filename}.html")
    with open(html_file, "w") as f:
        f.write(html_content)

    out_img = os.path.join(OUTPUT_DIR, filename)
    cmd = [
        CHROME,
        "--headless=new",
        f"--screenshot={out_img}",
        f"--window-size={width},{height}",
        f"file://{html_file}"
    ]
    subprocess.run(cmd, check=True)
    subprocess.run(["cp", out_img, os.path.join(DOCS_SCREENSHOT_DIR, filename)], check=True)
    print(f"Generated screenshot: {filename}")

# Clean up older backend_forms.py.png if present
old_file = os.path.join(OUTPUT_DIR, "backend_forms.py.png")
if os.path.exists(old_file):
    os.remove(old_file)
old_doc_file = os.path.join(DOCS_SCREENSHOT_DIR, "backend_forms.py.png")
if os.path.exists(old_doc_file):
    os.remove(old_doc_file)

print("All backend screenshots successfully generated!")
