from django.core.management.base import BaseCommand
#from inventory.models import User, Family, Category, Item, ItemTransaction, Checkin, Checkout, AgeRange
from inventory.models import Item, Checkin

# MIGRATION SCRIPT

class Command(BaseCommand):
    args = '<this func takes no args>'
    help = 'Run this script to migrate old database into newly designed one.'

    #NEW_ITEM_NAMES = ["shirt", "shoes", "underwear", "socks", "pj", "shorts", "pants", "sweater/sweartshirt", "coat/jacket", "dress/skirt", "accessories", "other", "snowsuit", "onesie"]
    NEW_ITEM_NAMES = []
    NEW_SIZES = ["baby", "toddler", "kid", "teen"]

    def map(itemName):
        item_mapped = "" 
        size_mapped = ""
        if ("boy" in itemName) or ("girl" in itemName):
            if itemName.startswith("boys "):
                name_new = itemName[len("boys "):]
                item_mapped = name_new.split()[0]
            elif itemName.startswith("girls "):
                name_new = itemName[len("girls "):]
                item_mapped = name_new.split()[0]
            elif itemName.endswith("boy)"): 
                name_new = itemName
                item_mapped = name_new.split()[0]
            elif itemName.endswith("girl)"):
                name_new = itemName
                item_mapped = name_new.split()[0]

            if (len(name_new.split()) > 1) and name_new.split()[1] == "socks":
                item_mapped = "socks"
            if ("snowsuit" in item_mapped):  #this branch is to cope with one typo, no subtle way to put this.
                item_mapped = "snowsuit"
            if ("coat" in item_mapped) or ("jacket" in item_mapped):
                    item_mapped = "coat/jacket"
            if "pj" in item_mapped:
                    item_mapped = "pj"

            if ("teen" in name_new) or ("14-16" in name_new) or ("18-20" in name_new):
                size_mapped = "teen"
            elif ("kid" in name_new) or ("6-7" in name_new) or ("8-10" in name_new) or ("10-12" in name_new) or ("12-14" in name_new):
                size_mapped = "kid"
            elif ("infant" in name_new) or (" mo" in name_new) or ("baby" in name_new):
                size_mapped = "baby"
            elif ("2T-3T" in name_new) or ("4T-5T" in name_new) or ("toddler" in name_new):
                size_mapped = "toddler"

        else:
            raise Exception("ill-formatted input string")
        return item_mapped, size_mapped


    def _update_items(self):
        for t in Item.objects.all():
            name = t.name
            if ("boys" in name) or ("girls" in name):
                item_mapped, size_mapped = map(name)
                item_new = Item.object.filter(name == item_mapped + " " + size_mapped)
                item_new.quantity += (t.quantity if t.quantity>0 else 0)


    def _add_items(self):
        for t in Item.objects.all():
            name = t.name
            if ("boys" in name) or ("girls" in name):
                item_mapped, size_mapped = map(name)
                if not(item_mapped in Command.NEW_ITEM_NAMES):
                    Command.NEW_ITEM_NAMES.append(item_mapped)
        # for item in Command.NEW_ITEM_NAMES:
        #     print(item)
        for item in Command.NEW_ITEM_NAMES:
            for size in Command.NEW_SIZES:
                # print("creating item: "+ item+" "+size +" \n")
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