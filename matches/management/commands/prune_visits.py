"""Deletes old page-view rows so the visit log does not grow forever.

    python manage.py prune_visits              # uses VISIT_TRACKING["RETENTION_DAYS"]
    python manage.py prune_visits --days 30    # keep only the last 30 days
"""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from matches.models import VisitLog


class Command(BaseCommand):
    help = "Delete visit log rows older than the retention period."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, help="keep this many days (default: settings.VISIT_TRACKING)")

    def handle(self, *args, **options):
        days = options["days"] or getattr(settings, "VISIT_TRACKING", {}).get("RETENTION_DAYS", 180)
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = VisitLog.objects.filter(visited_at__lt=cutoff).delete()
        self.stdout.write(f"Deleted {deleted} visit(s) older than {days} days.")
