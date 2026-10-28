import os
import django
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from polls.models import Question, Choice

User = get_user_model()

def seed():
    print("--- Seeding Database for Django PollMaster ---")

    # 1. Create Superuser for Django Admin
    username = "admin"
    password = "adminpassword123"
    email = "admin@example.com"
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"[✓] Superuser created: username='{username}', password='{password}'")
    else:
        print(f"[i] Superuser '{username}' already exists.")

    # 2. Clear existing demo questions
    Question.objects.all().delete()
    print("[✓] Cleared previous demo questions.")

    now = timezone.now()

    # 3. Create Sample Polls
    polls_data = [
        {
            "question_text": "What is your favorite Python web framework in 2026?",
            "pub_date": now - datetime.timedelta(hours=3),
            "is_active": True,
            "choices": [
                ("Django (Batteries Included & Robust)", 42),
                ("FastAPI (Async & High Performance)", 35),
                ("Flask (Lightweight & Minimalist)", 14),
                ("Litestar / Pyramid / Others", 7),
            ]
        },
        {
            "question_text": "Which cloud platform does your team rely on primarily?",
            "pub_date": now - datetime.timedelta(days=1),
            "is_active": True,
            "choices": [
                ("Google Cloud Platform (GCP)", 38),
                ("Amazon Web Services (AWS)", 45),
                ("Microsoft Azure", 22),
                ("Self-Hosted / Hybrid Cloud", 11),
            ]
        },
        {
            "question_text": "What is the primary factor when choosing a backend tech stack?",
            "pub_date": now - datetime.timedelta(days=2),
            "is_active": True,
            "choices": [
                ("Developer Productivity & Tooling", 58),
                ("Raw Performance & Scalability", 32),
                ("Community & Ecosystem Maturity", 40),
                ("Team Familiarity & Hiring Ease", 50),
            ]
        },
        {
            "question_text": "Archived: Which CSS approach do you use for rapid prototyping?",
            "pub_date": now - datetime.timedelta(days=15),
            "is_active": False,
            "choices": [
                ("Tailwind CSS", 65),
                ("Bootstrap", 25),
                ("Pure Modern CSS / Flexbox & Grid", 30),
                ("CSS-in-JS", 10),
            ]
        }
    ]

    for p in polls_data:
        question = Question.objects.create(
            question_text=p["question_text"],
            pub_date=p["pub_date"],
            is_active=p["is_active"]
        )
        for choice_text, votes in p["choices"]:
            Choice.objects.create(question=question, choice_text=choice_text, votes=votes)
        print(f"[✓] Created Poll: '{question.question_text}' with {len(p['choices'])} choices.")

    print("\nDatabase seeded successfully!")
    print(f"Total Questions: {Question.objects.count()}")
    print(f"Total Choices: {Choice.objects.count()}")

if __name__ == "__main__":
    seed()
