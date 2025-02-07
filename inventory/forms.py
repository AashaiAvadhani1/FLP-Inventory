from django import forms
from django.db.models import Q

from inventory.models import Item, Family, Category, AgeRange, ItemTransaction

from django.contrib.auth import authenticate
from phonenumber_field.formfields import PhoneNumberField

class LoginForm(forms.Form):
    username = forms.CharField(max_length = 20)
    password = forms.CharField(max_length = 200, widget = forms.PasswordInput())
    required_css_class = 'required'

    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()

        # Confirms that the two password fields match
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError("Invalid username/password")

        # We must return the cleaned data we got from our parent.
        return cleaned_data

class CreateFamilyForm(forms.Form):
    first_name = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control'}), required=False, label='Caregiver first name')
    last_name = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control'}), label='Caregiver last name')
    phone = PhoneNumberField(widget=forms.TextInput(attrs={'class': 'form-control', 'type':'tel'}),
                            required=False)
    required_css_class = 'required'

    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()

        # We must return the cleaned data we got from our parent.
        return cleaned_data

class CreateItemForm(forms.Form):
    category   = forms.ModelChoiceField(queryset=Category.objects.all(),
                                        widget=forms.Select(attrs={'class': 'form-select'}))
    name = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    new_price = forms.DecimalField(max_digits=6, decimal_places=2, required=False)
    used_price = forms.DecimalField(max_digits=6, decimal_places=2, required=False)
    required_css_class = 'required' 
    
    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()

        # We must return the cleaned data we got from our parent.
        return cleaned_data

    # Customizes form validation for the name field.
    def clean_name(self):
        # Confirms that the username is already present in the
        # Item model database.
        name = self.cleaned_data.get('name')
        if Item.objects.filter(name__exact=name):
            raise forms.ValidationError("Item already exists.")

        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return name 

    # Customizes form validation for the quantity field.
    def clean_quantity(self):
        # Confirms the quantity is above zero
        quantity = self.cleaned_data.get('quantity')

        if quantity < 0:
            raise forms.ValidationError("Quantity must be zero or above.")

        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return quantity

    # Customizes form validation for the new price field.
    def clean_new_price(self):
        # Confirms the new price is above zero
        price = self.cleaned_data.get('new_price')

        if price and price < 0:
            raise forms.ValidationError("New price must be above zero.")

        # We must return the cleaned data we got from the cleaned_data dictionary
        return price
    
    # Customizes form validation for the used price field.
    def clean_used_price(self):
        # Confirms the used price is above zero
        price = self.cleaned_data.get('used_price')

        if price and price < 0:
            raise forms.ValidationError("Used price must be above zero.")

        # We must return the cleaned data we got from the cleaned_data dictionary
        return price

class AddItemForm(forms.Form):
    item = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    new_quantity = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    used_quantity = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    required_css_class = 'required'

    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()

        used_quant = cleaned_data.get('used_quantity')
        new_quant = cleaned_data.get('new_quantity')

        #Checks that quantity input of both used and new quantity sums to greater than 0
        if used_quant==None and new_quant==None:
            raise forms.ValidationError("Total inputted quantity must be above zero.")

        # We must return the cleaned data we got from our parent.
        return cleaned_data

    # Customizes form validation for the name field.
    def clean_item(self):
        # Confirms that the username is already present in the
        # Item model database.
        name = self.cleaned_data.get('item')
        if not Item.objects.filter(name__exact=name):
            raise forms.ValidationError("Item does not exist.")

        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return name 

    def clean_used_quantity(self):
        # Confirms the quantity is above zero if a value is inputted
        used_quantity = self.cleaned_data.get('used_quantity')

        if used_quantity is not None and used_quantity <= 0:
            raise forms.ValidationError("Quantity must be above zero.")

        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return used_quantity

    def clean_new_quantity(self):
        # Confirms the quantity is above zero if a value is inputted
        new_quantity = self.cleaned_data.get('new_quantity')

        if new_quantity is not None and new_quantity <= 0:
           raise forms.ValidationError("Quantity must be above zero.")

        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return new_quantity

    
class CheckOutForm(forms.Form):
    family = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    required_css_class = 'required'
    child = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    age   = forms.ModelChoiceField(queryset=AgeRange.objects.all(),
                                        widget=forms.Select(attrs={'class': 'form-select'}))
    

    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()

        # We must return the cleaned data we got from our parent.
        return cleaned_data

    def clean_family(self):
        # Confirms the family exists
        family = self.cleaned_data.get('family').strip()

        if not Family.objects.filter(Q(displayName__exact=family)):
            raise forms.ValidationError("Family does not exist.")

        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return family

class AdminItemOutdateForm(forms.Form):
    Old_item = forms.CharField(max_length=50, required=True,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    New_item = forms.CharField(max_length=50, required=True,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    # required_css_class = 'required'

    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()
        
        # We must return the cleaned data we got from our parent.
        return cleaned_data

    # Customizes form validation for the name field.
    def clean_Old_item(self):
        # Confirms that the username is already present in the
        # Item model database.
        name = self.cleaned_data.get('Old_item')
        if not Item.objects.filter(name__exact=name):
            raise forms.ValidationError("This Old Item does not exist.")
        if not Item.objects.filter(name__exact=name, outdated__exact=False):
            raise forms.ValidationError("Item must not be outdated.")
        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return name 

    def clean_New_item(self):
        # Confirms that the username is already present in the
        # Item model database.
        name = self.cleaned_data.get('New_item')
        if not Item.objects.filter(name__exact=name):
            raise forms.ValidationError("Item does not exist.")
        if not Item.objects.filter(name__exact=name, outdated__exact=False):
            raise forms.ValidationError("Item must not be outdated.")
        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return name
    
    def run(self):
        self.clean()
        old_name = self.cleaned_data.get('Old_item')
        new_name = self.cleaned_data.get('New_item')
        old_item = Item.objects.get(name = old_name)
        new_item = Item.objects.get(name = new_name)
        if old_item.quantity > 0:   
            new_item.quantity = new_item.quantity + old_item.quantity
        new_item.save()
        
        for ins in ItemTransaction.objects.all():
            if ins.item_id == old_item.id:
                ins.item_id = new_item.id
                ins.save()
        
        old_item.outdated = True
        old_item.save()
        
    
