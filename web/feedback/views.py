"""The feedback page: a form whose messages are stored, then emailed to me."""

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import MessageForm
from .mailer import send_email_async
from .turnstile import verify_turnstile


def feedback(request: HttpRequest) -> HttpResponse:
    """
    Show the feedback form, and store each valid message.

    The footer link passes the page the sender came from as ?from=, which the form carries in a
    hidden field. A message that fails the Turnstile check is still stored, with captcha_passed
    False, but isn't emailed.
    """
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.captcha_passed = verify_turnstile(
                request.POST.get("cf-turnstile-response", ""), settings.TURNSTILE_SECRET_KEY
            )
            message.save()
            if message.captcha_passed:
                send_email_async(message)
            messages.success(request, "Thankyou!")
            messages.info(request, "NB: I endeavour to respond within 48 hours.")
            return redirect("feedback")
    else:
        form = MessageForm(initial={"page": request.GET.get("from", "")})
    context = {"form": form, "turnstile_site_key": settings.TURNSTILE_SITE_KEY}
    return render(request, "feedback/feedback.html", context)
