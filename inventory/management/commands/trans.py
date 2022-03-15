from django.core.management.base import BaseCommand
from inventory.models import User, Family, Category, Item, ItemTransaction, Checkin, Checkout, AgeRange

# DROP SCRIPT

class Command(BaseCommand):
    args = '<this func takes no args>'
    help = 'Run this script to change old database into newly designed one.'

    def _update_users(self):
        User.objects.all().delete() 

        print("Users deleted.")

    def _update_families(self):
        Family.objects.all().delete() 

        print("Families deleted.")

    def _update_age_ranges(self):
        AgeRange.objects.all().delete() 

        print("AgeRanges deleted.")

    def _update_categories(self):
        Category.objects.all().delete() 

        print("Categories deleted.")

    def _update_items(self):
        for t in Item.objects.all():
            print(t.outdated)
            t.outdated = False
            print(t.outdated)

        print("Items update.")

    def _update_item_transactions(self):
        ItemTransaction.objects.all().delete() 

        print("ItemTransactions deleted.")

    def _update_checkins(self):
        
        print(Checkin.objects.all())
        print("\nCheckins updated.")

    def _update_checkouts(self):
        Checkout.objects.all().delete() 

        print("Checkouts deleted.")

    def handle(self, *args, **options):
        # self._update_checkins()
        # self._update_checkouts()
        # self._update_item_transactions()
        self._update_items()
        # self._update_categories()
        # self._update_age_ranges()
        # self._update_families()
        # self._update_users()
