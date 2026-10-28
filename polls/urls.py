from django.urls import path
from . import views

app_name = "polls"

urlpatterns = [
    # Unified Single Web Application
    path("", views.single_app_view, name="index"),
    path("app/", views.single_app_view, name="single_app"),

    # REST APIs for dynamic single-page transitions
    path("api/polls/", views.api_polls, name="api_polls"),
    path("api/polls/<int:pk>/", views.api_poll_detail, name="api_poll_detail"),
    path("api/polls/<int:pk>/vote/", views.api_vote, name="api_vote"),
    path("api/polls/create/", views.api_create, name="api_create"),

    # Traditional Multi-Page Views (for direct deep links / SEO / bookmarks)
    path("list/", views.IndexView.as_view(), name="list"),
    path("create/", views.poll_create, name="create"),
    path("dashboard/", views.analytics_dashboard, name="dashboard"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:pk>/vote/", views.vote, name="vote"),
]
