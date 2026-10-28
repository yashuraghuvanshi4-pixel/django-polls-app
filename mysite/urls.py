"""
mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

urlpatterns = [
    # Root redirects to polls index
    path("", lambda request: redirect("polls:index")),
    # Polls application URLs
    path("polls/", include("polls.urls")),
    # Django Built-in Admin Interface
    path("admin/", admin.site.urls),
]
