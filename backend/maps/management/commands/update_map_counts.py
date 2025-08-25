from django.core.management import base
from django.db import transaction
from django.db.models import Count

from maps.models import Map, AuthorCategoryCounter, AuthorTagCounter

class Command(base.BaseCommand):
    help = "Rebuild database counters (AuthorCategoryCounter, AuthorTagCounter) from Map data"

    def handle(self, *args, **options):
        self.stdout.write("Rebuilding counters...")

        self.stdout.write("Rebuilding AuthorCategoryCounter...")
        qs = Map.objects.values('author_id', 'category').annotate(cnt=Count('pk'))
        acc_objs = [
            AuthorCategoryCounter(author_id=item['author_id'], category=item['category'], map_count=item['cnt'])
            for item in qs
        ]
        with transaction.atomic():
            AuthorCategoryCounter.objects.all().delete()
            if acc_objs:
                AuthorCategoryCounter.objects.bulk_create(acc_objs, batch_size=1000)

        self.stdout.write("Rebuilding AuthorTagCounter...")
        tag_map = {}
        maps_with_tags = Map.objects.exclude(tags=[]).values('author_id', 'tags')
        for item in maps_with_tags:
            author_id = item['author_id']
            for tag in item['tags'] or []:
                key = (author_id, tag)
                tag_map[key] = tag_map.get(key, 0) + 1

        with transaction.atomic():
            AuthorTagCounter.objects.all().delete()
            tag_objs = [
                AuthorTagCounter(author_id=aid, tag=tag, map_count=count)
                for (aid, tag), count in tag_map.items()
            ]
            if tag_objs:
                AuthorTagCounter.objects.bulk_create(tag_objs, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS('Counters rebuilt successfully.')
        )