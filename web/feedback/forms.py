"""The feedback form."""

from django import forms

from .models import Message


class MessageForm(forms.ModelForm[Message]):
    """Name, email and message, with the page the sender came from as a hidden field."""

    class Meta:
        model = Message
        fields = ("name", "email", "text", "page")
        widgets = {  # noqa: RUF012 - Django reads this dict; nothing mutates it
            "text": forms.Textarea(attrs={"rows": 6}),
            "page": forms.HiddenInput,
        }
