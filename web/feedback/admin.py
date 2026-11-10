"""Feedback messages in the admin, newest first."""

from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin[Message]):
    list_display = ("received", "name", "email", "page", "captcha_passed", "email_sent")
    list_filter = ("captcha_passed", "email_sent")
    search_fields = ("name", "email", "text")
