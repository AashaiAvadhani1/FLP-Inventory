from django.core.management.base import BaseCommand
from inventory.models import User, Family, Category, Item, ItemTransaction, Checkin, Checkout, AgeRange
import re

# DROP SCRIPT

class Command(BaseCommand):
    args = '<this func takes no args>'
    help = 'Run this script to migrate old database into newly designed one.'

    #NEW_ITEM_NAMES = ["shirt", "shoes", "underwear", "socks", "pj", "shorts", "pants", "sweater/sweartshirt", "coat/jacket", "dress/skirt", "accessories", "other", "snowsuit", "onesie"]
    NEW_ITEM_NAMES = []
    NEW_SIZES = ["baby", "toddler", "kid", "teen"]

    def map(itemName):
        if itemName == "snowsuit":
            return "coat"


    def _update_items(self):
        for t in Item.objects.all():
            name = t.name
            x = re.match("^(boys|girls)", name)
            if x:
                print(name)
                if name.startswith("boys "):
                    name_new = name[len("boys "):]
                    item_mapped = name_new.split()[0]
                elif name.startswith("girls "):
                    name_new = name[len("girls "):]
                    item_mapped = name_new.split()[0]
                elif name.endswith("boy)"):
                    name_new = name
                    item_mapped = name.split()[0]
                elif name.endswith("girls)"):
                    name_new = name
                    item_mapped = name.split()[0]

                #print(item_mapped)
                if (len(name_new.split()) > 1) and name_new.split()[1] == "socks":
                    item_mapped = "socks"
                if ("snowsuit" in item_mapped):  #this branch is to cope with one typo, no subtle way to put this.
                    item_mapped = "snowsuit"
                
                print(item_mapped)

                if ("teen" in name_new) or ("14-16" in name_new) or ("18-20" in name_new):
                    size_mapped = "teen"
                elif ("kid" in name_new) or ("6-7" in name_new) or ("8-10" in name_new) or ("10-12" in name_new) or ("12-14" in name_new):
                    size_mapped = "kid"
                elif ("infant" in name_new) or (" mo" in name_new):
                    size_mapped = "baby"
                elif ("2T-3T" in name_new) or ("4T-5T" in name_new):
                    size_mapped = "toddler"

                print(size_mapped+"\n")

                # item_new = Item.object.filter(name == item_mapped + " " + size_mapped)
                # item_new.quantity += (t.quantity if t.quantity>0 else 0)


    def _add_items(self):
        for t in Item.objects.all():
            name = t.name
            x = re.match("^(boys|girls)", name)
            if x:
                if name.startswith("boys "):
                    name_new = name[len("boys "):]
                    item_mapped = name_new.split()[0]
                elif name.startswith("girls "):
                    name_new = name[len("girls "):]
                    item_mapped = name_new.split()[0]
                elif name.endswith("boy)"):
                    name_new = name
                    item_mapped = name.split()[0]
                elif name.endswith("girls)"):
                    name_new = name
                    item_mapped = name.split()[0]

                #print(item_mapped)
                item_mapped = item_mapped.lower()
                if (len(name_new.split()) > 1) and name_new.split()[1] == "socks":
                    item_mapped = "socks"
                if ("snowsuit" in item_mapped):  #this branch is to cope with one typo, no subtle way to put this.
                    item_mapped = "snowsuit"
                #TODO: add same item merges, e.g. coat, jacket -> coat/jacket
                if ("coat" in item_mapped) or ("jacket" in item_mapped):
                    item_mapped = "coat/jacket"
                if "pj" in item_mapped:
                    item_mapped = "pj"

                if not(item_mapped in Command.NEW_ITEM_NAMES):
                    Command.NEW_ITEM_NAMES.append(item_mapped)

        for item in Command.NEW_ITEM_NAMES:
            print(item)
        for item in Command.NEW_ITEM_NAMES:
            for size in Command.NEW_SIZES:
                print("creating item: "+ item+" "+size +" \n")
                Item.objects.create(name=item+" "+size, quantity=0)
                print("created item: "+ item+" "+size +" \n")
            

    def _add_outdated(self):
        for t in Item.objects.all():
            print(t.outdated)
            t.outdated = False
            print(t.outdated)

        print("Items update.")

    def _update_checkins(self):
        for ins in Checkin.objects.all():
            print(ins)


    def handle(self, *args, **options):
        # self._add_outdated()
        self._add_items()
        # self._update_items()
        # self._update_checkins()
        # self._update_checkouts()
        # self._update_item_transactions()
        # self._update_categories()
        # self._update_age_ranges()
        # self._update_families()
        # self._update_users()


# WANT: Baby, kid, toddler, teen

# From Tomas Viejobueno to Everyone 11:33 AM
# CURRENT: 0-24 mo -> baby
# 2-14-> kid
# 14-20 -> teen
# 2-5 -> toddler
# 6-14 -> kid
# 14-20 -> teen
# 2-5, infant -> toddler
# 0-24 mo, infant -> baby
# 2T-5T, toddler -> toddler
# 6-14, kid -> kid
# 14-20, teen -> teen

# From Harriet Khang to Everyone 11:40 AM
# Shirt 
# Pant
# Underwear
# Socks 
# Pjs
# Shoe
# Toy		
# Blanket
# Hygiene kit 
# Stuffed Animal

# From Tomas Viejobueno to Everyone 11:41 AM
# Items: shirt, shoes, underwear, socks, pjs, shorts, pants, sweater, coat/jacket, dress/skirt

# aggregate all checkouts items, delete others