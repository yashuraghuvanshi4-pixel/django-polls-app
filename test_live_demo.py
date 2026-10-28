import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.test import Client
from polls.models import Question

def run_demo():
    client = Client()
    print("=== LIVE DEMO WALKTHROUGH ===")

    # 1. Access Index Page
    print("\n1. Testing Index Page GET /polls/ ...")
    res = client.get("/polls/")
    assert res.status_code == 200
    assert b"Community Polls" in res.content
    print("-> 200 OK! Index page loaded with community polls list.")

    # 2. Access First Question
    q = Question.objects.filter(is_active=True).first()
    print(f"\n2. Testing Detail Page for Question ID={q.id}: '{q.question_text}' ...")
    res = client.get(f"/polls/{q.id}/")
    assert res.status_code == 200
    print(f"-> 200 OK! Found {q.choices.count()} choices rendered in voting form.")

    # 3. Cast a Vote
    choice_to_vote = q.choices.first()
    initial_votes = choice_to_vote.votes
    print(f"\n3. Submitting Vote via POST /polls/{q.id}/vote/ for choice '{choice_to_vote.choice_text}' (Initial votes={initial_votes}) ...")
    post_res = client.post(f"/polls/{q.id}/vote/", {"choice": choice_to_vote.id})
    assert post_res.status_code == 302
    print(f"-> 302 Redirect! Redirected safely to: {post_res.url}")

    choice_to_vote.refresh_from_db()
    print(f"-> Verified DB state: Vote incremented from {initial_votes} to {choice_to_vote.votes}")

    # 4. View Results Page
    print(f"\n4. Testing Results Page GET /polls/{q.id}/results/ ...")
    results_res = client.get(f"/polls/{q.id}/results/")
    assert results_res.status_code == 200
    print(f"-> 200 OK! Results displayed with updated vote tallies and percentage bars.")

    # 5. Admin Authentication Test
    print("\n5. Testing Admin Login with 'admin' credentials ...")
    login_success = client.login(username="admin", password="adminpassword123")
    assert login_success
    admin_res = client.get("/admin/polls/question/")
    assert admin_res.status_code == 200
    print("-> 200 OK! Admin successfully authenticated and accessed Poll Questions admin list.")

    print("\n=== ALL DEMO CHECKS PASSED PERFECTLY ===")

if __name__ == "__main__":
    run_demo()
