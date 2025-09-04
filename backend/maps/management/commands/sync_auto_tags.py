from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = (
        "Synchronizes automatic tags from map data."
    )

    def handle(self, *args, **options):
        from maps.models import Map
        from maps.utils import is_autowin

        processed = 0
        added = 0
        removed = 0
        errors = 0

        qs = Map.objects.all().only('xml', 'tags')

        for m in qs.iterator():
            processed += 1
            xml = m.xml
            tags = m.tags or []

            try:
                result = bool(is_autowin(xml))
            except Exception as exc:
                errors += 1
                self.stderr.write(
                    f"[ERROR] Map {m.pk}: is_autowin raised {exc!r} — skipping."
                )
                continue

            has_tag = 'autowin' in tags

            if result and not has_tag:
                new_tags = tags + ['autowin']
                with transaction.atomic():
                    Map.objects.filter(pk=m.pk).update(tags=new_tags)
                added += 1
                self.stdout.write(f"[ADD] Map {m.pk}: added 'autowin'")

            elif (not result) and has_tag:
                new_tags = [t for t in tags if t != 'autowin']
                with transaction.atomic():
                    Map.objects.filter(pk=m.pk).update(tags=new_tags)
                removed += 1
                self.stdout.write(f"[REMOVE] Map {m.pk}: removed 'autowin'")

        self.stdout.write(f"Processed: {processed}")
        self.stdout.write(f"Added: {added}")
        self.stdout.write(f"Removed: {removed}")
