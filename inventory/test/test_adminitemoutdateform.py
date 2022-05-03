from unicodedata import name
from django.test import TestCase

from inventory.forms import AdminItemOutdateForm
from inventory.models import Item, ItemTransaction

class AddItemFormTestCase(TestCase):
    def setUp(self):
        olditem = Item.objects.create(name="OldItem", quantity=5, outdated=False)
        newitem = Item.objects.create(name="NewItem", quantity=1, outdated=False)
        outdateditem = Item.objects.create(name="OutdatedItem", quantity=5, outdated=True)
        olditem.save()
        newitem.save()
        outdateditem.save()

    def test_invalid_required_fields(self):
        form = AdminItemOutdateForm(data={})

        self.assertFalse(form.is_valid())

        self.assertEqual(
            form.errors["item_old"], ["This field is required."]
        )

    def test_invalid_does_not_exist(self):
        form = AdminItemOutdateForm(data={"item_old": "InvalidItem", "item_new": "NewItem"})

        self.assertFalse(form.is_valid())

        self.assertEqual(
            form.errors["item_old"], ["Item does not exist."]
        )
        
    def test_invalid_outdated_old_item(self):
        form = AdminItemOutdateForm(data={"item_old": "OutdatedItem", "item_new": "NewItem"})

        self.assertEqual(
            form.errors["item_old"], ["Item must not be outdated."]
        )
        
    def test_invalid_outdated_new_item(self):
        form = AdminItemOutdateForm(data={"item_old": "OldItem", "item_new": "OutdatedItem"})

        self.assertEqual(
            form.errors["item_new"], ["Item must not be outdated."]
        )

    def test_valid(self):
        form = AdminItemOutdateForm(data={"item_old": "OldItem", "item_new": "NewItem"})

        self.assertTrue(form.is_valid())

    def test_run(self):
        form = AdminItemOutdateForm(data={"item_old": "OldItem", "item_new": "NewItem"})
        self.assertTrue(form.is_valid())
        form.run()

        self.assertEqual(Item.objects.get(name="OldItem").outdated, True)
        self.assertEqual(Item.objects.get(name="NewItem").outdated, False)
        self.assertEqual(Item.objects.get(name="NewItem").quantity, 6)

