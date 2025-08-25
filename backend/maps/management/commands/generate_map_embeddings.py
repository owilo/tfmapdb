from django.core.management.base import BaseCommand
from django.db import transaction
from maps.models import Map
from maps.embeddings import embed_from_xml

class Command(BaseCommand):
    help = 'Regenerates embeddings for all maps using XML content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of maps to process in a single batch (default: 100)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        maps = Map.objects.all()
        total_maps = maps.count()

        self.stdout.write(f'Regenerating embeddings for {total_maps} maps...')

        with transaction.atomic():
            for i in range(0, total_maps, batch_size):
                batch = maps[i:i + batch_size]
                updated_maps = []
                
                for map in batch:
                    try:
                        embedding_array = embed_from_xml(map.xml)
                        map.embedding = embedding_array.tolist()
                        updated_maps.append(map)
                    except Exception as e:
                        self.stderr.write(
                            f'Failed to process map {map.code}: {str(e)}'
                        )

                Map.objects.bulk_update(updated_maps, ['embedding'])
                
                self.stdout.write(
                    f'Processed {min(i + batch_size, total_maps)}/{total_maps} maps'
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully regenerated all embeddings')
        )