from django.test import TestCase

from inventory.forms import AddItemForm
from inventory.models import Item

class MigrationDatabase(TestCase):
    
    #The setup that can test the map function
    def setUp(self):
                
        
        #populate items that start with boy 
        starts_with_boy = ["boy pants", "boy pants", "0", 0]
        #populate items that  start with girl
        starts_with_girl = ["girl pants", "girl pants", "0", 0]
        #populate items that end with boy
        end_with_boy = ["pants boy", "pants boys","pants girl", "pants girl", "boy pants", "0", 0]

        #populate items that end with girl 
        end_with_girl = ["pants girl", "pants girl","pants girl", "pantsgirlpants", "girl pants", "0", 0]

    def test_map_function():
        pass

