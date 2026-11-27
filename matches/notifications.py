"""Email notices for roommate requests (they print in the terminal while EMAIL_BACKEND is the console)."""
from django.conf import settings
from django.core.mail import send_mail


def _name(user):
    profile = getattr(user, "profile", None)
    return profile.full_name if profile else user.email


def notify_new_request(req, inbox_url):
    names = {"receiver": _name(req.receiver), "sender": _name(req.sender), "site": settings.SITE_NAME}
    body = "Hi %(receiver)s,\n\n%(sender)s sent you a roommate request on %(site)s.\n" % names
    if req.message:
        body += '\nTheir message: "%(message)s"\n' % {"message": req.message}
    body += "\nAccept or decline it here: %(url)s\n\n%(site)s\n" % {"url": inbox_url, "site": settings.SITE_NAME}
    send_mail("New roommate request from %(sender)s" % names, body,
              settings.DEFAULT_FROM_EMAIL, [req.receiver.email], fail_silently=True)


def notify_response(req, inbox_url):
    names = {"receiver": _name(req.receiver), "sender": _name(req.sender), "site": settings.SITE_NAME,
             "status": req.get_status_display().lower()}
    body = "Hi %(sender)s,\n\n%(receiver)s %(status)s your roommate request.\n\nSee your requests: %(url)s\n\n%(site)s\n" % {
        **names, "url": inbox_url}
    send_mail("Your roommate request was %(status)s" % names, body,
              settings.DEFAULT_FROM_EMAIL, [req.sender.email], fail_silently=True)
