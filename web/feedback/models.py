"""Messages sent from the site's feedback form."""

from django.db import models


class Message(models.Model):
    """One message from the feedback form, stored before it is emailed."""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    text = models.TextField("message")
    page = models.TextField(blank=True, help_text="The page the sender came from.")
    received = models.DateTimeField(auto_now_add=True)
    captcha_passed = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ("-received",)

    def __str__(self) -> str:
        return f"{self.name}: {self.text[:50]}"
