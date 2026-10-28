from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Question, Choice


class VoteForm(forms.Form):
    """
    Form to handle and validate a user's vote on a specific Question.
    Dynamically binds the choices belonging only to that question.
    """
    choice = forms.ModelChoiceField(
        queryset=Choice.objects.none(),
        widget=forms.RadioSelect(attrs={"class": "poll-radio-input"}),
        empty_label=None,
        error_messages={
            "required": "You didn't select a choice. Please choose an option before voting.",
            "invalid_choice": "The selected choice is invalid for this poll.",
        }
    )

    def __init__(self, *args, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        if question is not None:
            self.fields["choice"].queryset = question.choices.all()

    def clean(self):
        cleaned_data = super().clean()
        if self.question and not self.question.is_active:
            raise ValidationError("This poll is closed and no longer accepting votes.")
        return cleaned_data


class PollCreateForm(forms.Form):
    """
    User-facing form to create a new Question and multiple Choices in one step.
    Enforces minimum 2 choices and non-empty inputs.
    """
    question_text = forms.CharField(
        max_length=200,
        label="Poll Question",
        help_text="Ask a clear, concise question for your audience.",
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "e.g., What is your favorite programming language in 2026?",
            "autocomplete": "off"
        })
    )
    choice_1 = forms.CharField(
        max_length=200,
        label="Option 1",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "First option (Required)"})
    )
    choice_2 = forms.CharField(
        max_length=200,
        label="Option 2",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Second option (Required)"})
    )
    choice_3 = forms.CharField(
        max_length=200,
        required=False,
        label="Option 3 (Optional)",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Third option"})
    )
    choice_4 = forms.CharField(
        max_length=200,
        required=False,
        label="Option 4 (Optional)",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Fourth option"})
    )
    choice_5 = forms.CharField(
        max_length=200,
        required=False,
        label="Option 5 (Optional)",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Fifth option"})
    )
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        label="Activate poll immediately for voting"
    )

    def clean(self):
        cleaned = super().clean()
        c1 = cleaned.get("choice_1", "").strip()
        c2 = cleaned.get("choice_2", "").strip()
        if c1 and c2 and c1.lower() == c2.lower():
            raise ValidationError("Option 1 and Option 2 cannot be identical.")
        return cleaned

    def save(self):
        """Creates Question and related Choice objects in the database."""
        question = Question.objects.create(
            question_text=self.cleaned_data["question_text"].strip(),
            pub_date=timezone.now(),
            is_active=self.cleaned_data.get("is_active", True)
        )
        for field in ["choice_1", "choice_2", "choice_3", "choice_4", "choice_5"]:
            choice_text = self.cleaned_data.get(field, "").strip()
            if choice_text:
                Choice.objects.create(question=question, choice_text=choice_text, votes=0)
        return question
