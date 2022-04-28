from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.conf.urls import url
# Register your models here.

from .models import Family, Category, Item, ItemTransaction, Checkin, Checkout, AgeRange
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from .forms import AdminItemOutdateForm

class FamilyAdmin(admin.ModelAdmin):
    list_display = ('id', 'fname', 'lname', 'phone', )
admin.site.register(Family, FamilyAdmin)

class AgeRangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'low', 'high', )
admin.site.register(AgeRange, AgeRangeAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
admin.site.register(Category, CategoryAdmin)

class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'quantity', 'new_price', 'used_price', 'outdated', 'item_actions', )
    # def item_actions(self, obj):
        
        
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r'^(?P<item_id>.+)/outdate/$',
                self.admin_site.admin_view(self.process_outdate),
                name='item-outdate',
            ),
        ]
        return custom_urls + urls
    
    def item_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Outdate</a>',
            reverse('admin:item-outdate', args=[obj.pk]),
        )
    item_actions.short_description = 'item Actions'
    item_actions.allow_tags = True
    
    def process_outdate(self, request, item_id, *args, **kwargs):
        return self.process_action(
            request=request,
            item_id=item_id,
            action_form=AdminItemOutdateForm,
            action_title='Outdate',
        )
        
    def process_action(
        self,
        request,
        item_id,
        action_form,
        action_title
    ):
        item = self.get_object(request, item_id)
        if request.method != 'POST':
            form = action_form()
        else:
            
            form = action_form(request.POST)
            if form.is_valid():
                try:
                    form.save(item, request.user)
                except errors.Error as e:
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
                    pass
                else:
                    self.message_user(request, 'Success')
                    url = reverse(
                        'admin:item_item_change',
                       args=[item.pk],
                        current_app=self.admin_site.name,
                    )
                    return HttpResponseRedirect(url)
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['item'] = item
        context['title'] = action_title
        print(str(request.POST))
        return TemplateResponse(
            request,
            'inventory/admin/item/outdate_action.html',
            context,
        )
    
admin.site.register(Item, ItemAdmin)

class ItemTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'quantity', 'is_new', )
admin.site.register(ItemTransaction, ItemTransactionAdmin)

class CheckinAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'in_items', 'datetime', )
admin.site.register(Checkin, CheckinAdmin)

class CheckoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'family', 'childName', 'ageRange', 'out_items', 'datetime', 'notes', )
admin.site.register(Checkout, CheckoutAdmin)
