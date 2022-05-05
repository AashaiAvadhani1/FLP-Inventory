from django.core.management.base import BaseCommand
from inventory.models import Item

class Command(BaseCommand):
    args = '<this func takes no args>'
    help = 'Run this script to make all items with negative quantities have 0 .'

    def _sanitize(self):
        for item in Item.objects.all():
            item.quantity = item.quantity if item.quantity>0 else 0
            item.save()

        print("Done.")

    def handle(self, *args, **options):
        self._sanitize()

