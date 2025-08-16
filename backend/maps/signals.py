from django.db import transaction, IntegrityError
from django.db.models import F
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .models import Map, AuthorCategoryCounter, AuthorTagCounter

def increment_author_category(author_id, category):
    """
    Increment (author, category) counter.
    Returns True if a new AuthorCategoryCounter row was created.
    """
    created = False
    while True:
        try:
            with transaction.atomic():
                try:
                    # Lock the existing row if present
                    acc = AuthorCategoryCounter.objects.select_for_update().get(author_id=author_id, category=category)
                    AuthorCategoryCounter.objects.filter(pk=acc.pk).update(map_count=F('map_count') + 1)
                    created = False
                except AuthorCategoryCounter.DoesNotExist:
                    # Try to create the row. If another transaction created it concurrently, raise IntegrityError and retry
                    try:
                        AuthorCategoryCounter.objects.create(author_id=author_id, category=category, map_count=1)
                        created = True
                    except IntegrityError:
                        raise
            break
        except IntegrityError:
            # Retry on concurrent insertion
            continue
    return created


def decrement_author_category(author_id, category):
    """
    Decrement (author, category) counter. Delete row if it reaches zero.
    """
    while True:
        try:
            with transaction.atomic():
                try:
                    acc = AuthorCategoryCounter.objects.select_for_update().get(author_id=author_id, category=category)
                except AuthorCategoryCounter.DoesNotExist:
                    return

                if acc.map_count > 1:
                    AuthorCategoryCounter.objects.filter(pk=acc.pk).update(map_count=F('map_count') - 1)
                else:
                    AuthorCategoryCounter.objects.filter(pk=acc.pk).delete()
            break
        except IntegrityError:
            continue


def increment_author_tag(author_id, tag):
    """
    Increment (author, tag) counter.
    Returns True if a new AuthorTagCounter row was created.
    """
    created = False
    while True:
        try:
            # Lock the existing row if present
            with transaction.atomic():
                try:
                    atc = AuthorTagCounter.objects.select_for_update().get(author_id=author_id, tag=tag)
                    AuthorTagCounter.objects.filter(pk=atc.pk).update(map_count=F('map_count') + 1)
                    created = False
                except AuthorTagCounter.DoesNotExist:
                    # Try to create the row. If another transaction created it concurrently, raise IntegrityError and retry
                    try:
                        AuthorTagCounter.objects.create(author_id=author_id, tag=tag, map_count=1)
                        created = True
                    except IntegrityError:
                        raise
            break
        except IntegrityError:
            continue
    return created


def decrement_author_tag(author_id, tag):
    """
    Decrement (author, tag) counter. Delete row if it reaches zero.
    """
    while True:
        try:
            with transaction.atomic():
                try:
                    atc = AuthorTagCounter.objects.select_for_update().get(author_id=author_id, tag=tag)
                except AuthorTagCounter.DoesNotExist:
                    return

                if atc.map_count > 1:
                    AuthorTagCounter.objects.filter(pk=atc.pk).update(map_count=F('map_count') - 1)
                else:
                    AuthorTagCounter.objects.filter(pk=atc.pk).delete()
            break
        except IntegrityError:
            continue


# Map signal handlers

@receiver(pre_save, sender=Map)
def map_pre_save(sender, instance, **kwargs):
    """
    Capture previous values so post_save can compute deltas.
    """
    if instance._state.adding:
        instance._is_new = True
        instance._old_author_id = None
        instance._old_category = None
        instance._old_tags = []
    else:
        try:
            old = Map.objects.get(pk=instance.pk)
            instance._is_new = False
            instance._old_author_id = old.author_id
            instance._old_category = old.category
            instance._old_tags = list(old.tags or [])
        except Map.DoesNotExist:
            instance._is_new = True
            instance._old_author_id = None
            instance._old_category = None
            instance._old_tags = []


@receiver(post_save, sender=Map)
def map_post_save(sender, instance, created, **kwargs):
    """
    Maintain counters on map creation and update.
    """
    # Increment counters on map creation
    if created or getattr(instance, '_is_new', False):
        increment_author_category(instance.author_id, instance.category)
        for tag in (instance.tags or []):
            increment_author_tag(instance.author_id, tag)
        return

    # Update path
    old_author_id = getattr(instance, '_old_author_id', None)
    old_category = getattr(instance, '_old_category', None)
    old_tags = getattr(instance, '_old_tags', [])

    new_author_id = instance.author_id
    new_category = instance.category
    new_tags = list(instance.tags or [])

    # If author or category changed
    if (old_author_id is not None) and ((old_author_id != new_author_id) or (old_category != new_category)):
        decrement_author_category(old_author_id, old_category)
        increment_author_category(new_author_id, new_category)

    old_set = set(old_tags)
    new_set = set(new_tags)

    # If author changed, move all tags from old_author to new_author
    # I don't think it can happen, but it costs nothing to be safe
    if old_author_id is not None and old_author_id != new_author_id:
        for t in old_set:
            decrement_author_tag(old_author_id, t)
        for t in new_set:
            increment_author_tag(new_author_id, t)
    else:
        removed = old_set - new_set
        added = new_set - old_set
        for t in removed:
            decrement_author_tag(new_author_id, t)
        for t in added:
            increment_author_tag(new_author_id, t)


@receiver(post_delete, sender=Map)
def map_post_delete(sender, instance: Map, **kwargs):
    """
    Decrement counters on delete.
    """
    if instance.author_id is not None and instance.category is not None:
        decrement_author_category(instance.author_id, instance.category)

    for tag in (instance.tags or []):
        decrement_author_tag(instance.author_id, tag)
