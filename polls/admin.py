from django.contrib import admin
from .models import Question, Choice

# Customize Admin Site Branding
admin.site.site_header = "PollMaster Administration"
admin.site.site_title = "PollMaster Admin Portal"
admin.site.index_title = "Polls & Voting Management Dashboard"


class ChoiceInline(admin.TabularInline):
    """
    Allows managing choices directly inside the Question admin page.
    """
    model = Choice
    extra = 3
    fields = ("choice_text", "votes")
    readonly_fields = ()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Poll Questions with inline choices,
    filters, search, and bulk management actions.
    """
    fieldsets = [
        (
            "Question Details",
            {
                "fields": ["question_text", "is_active"],
                "description": "Specify the main question prompt and whether it is open for voting."
            }
        ),
        (
            "Publication Schedule",
            {
                "fields": ["pub_date"],
                "classes": ["collapse"],
                "description": "Configure when this poll should be published to users."
            }
        ),
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
    list_per_page = 20

    actions = ["activate_polls", "deactivate_polls", "reset_all_votes"]

    @admin.display(description="Total Votes")
    def total_votes_display(self, obj):
        return obj.total_votes()

    @admin.action(description="Mark selected polls as Active")
    def activate_polls(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        self.message_user(request, f"{rows_updated} poll(s) successfully marked as active.")

    @admin.action(description="Mark selected polls as Inactive")
    def deactivate_polls(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        self.message_user(request, f"{rows_updated} poll(s) successfully marked as inactive.")

    @admin.action(description="Reset vote counts for selected polls")
    def reset_all_votes(self, request, queryset):
        total_reset = 0
        for question in queryset:
            count = question.choices.update(votes=0)
            total_reset += count
        self.message_user(request, f"Votes reset to 0 across {total_reset} choices.")


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    """
    Allows standalone inspection and filtering of all individual choices.
    """
    list_display = ["choice_text", "question", "votes"]
    list_filter = ["question"]
    search_fields = ["choice_text", "question__question_text"]
