import json
import calendar
import csv
import io
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core import serializers
from django.http import JsonResponse
from django_tables2 import SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from .filters import CheckoutFilter, ItemFilter
from .tables import FamilyTable, CategoryTable, ItemTable, CheckinTable, CheckoutTable

from django.contrib import messages
from django.http import HttpResponse

from inventory.gdrive import get_auth_url, create_service, upload_to_gdrive, set_gdrive_message

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Count, Q

from inventory.models import Family, Category, Item, Checkin, Checkout, ItemTransaction
from inventory.forms import LoginForm, AddItemForm, CheckOutForm, CreateFamilyForm, CreateItemForm

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict

DEFAULT_PAGINATION_SIZE = 25
LOW_QUANTITY_THRESHOLD = 10 # this number or below is considered low quantity

######################### BASIC VIEWS #########################

# Handles home page render
def home(request): 
	return render(request, 'inventory/home.html')

# Handles about page render
def about(request):
	return render(request, 'inventory/about.html')

# Handles privacy policy page render
def privacy_policy(request):
    return render(request, 'inventory/policy.html')

######################### AUTH VIEWS ##########################

# Handles login
def login_action(request):
    context = {}

    if request.method == 'GET':
        context['form'] = LoginForm()
        return render(request, 'inventory/login.html', context)

    form = LoginForm(request.POST)
    context['form'] = form

    if not form.is_valid():
        return render(request, 'inventory/login.html', context)

    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])

    login(request, new_user)
    return redirect(reverse('Home'))

# Handles logout
def logout_action(request):
    logout(request)
    return redirect(reverse('Login'))

######################### REPORT GENERATION #########################

# Handles generate report page
@login_required(login_url='login')
def generate_report(request):
    context = {}
    refresh_session_keys(request)

    # If Generate Report Form was filled, it enters
    if ('start-date' in request.POST \
        and 'end-date' in request.POST \
        and 'tx-type' in request.POST \
        and (request.POST['tx-type'] in ['Checkin', 'Checkout'])) \
        or 'code' in request.GET \
        or 'error' in request.GET:

        if 'code' in request.GET \
            or 'error' in request.GET:
            set_context_vars_get(request, context)
        else: 
            set_context_vars_post(request, context)
        
        set_gdrive_message(request, context)
                
        # Checkout Group By Item (Export to Device)        
        if 'export' in request.POST:
            response = HttpResponse()
            response['Content-Disposition'] = 'attachment; filename=Checkout Report By Item ' + request.POST['start-date'] + " to " + request.POST['end-date'] + '.csv'
            return write_export_data(request, context, response)

        # Checkout Group By Item (Export to GDrive)        
        if 'export_drive' in request.POST \
            or 'export_drive' in request.session:

            si = io.StringIO()

            # If original POST Req, redirect to GAuth
            # If successful GET REQ from GAuth, write data & upload
            if 'code' not in request.GET \
                and 'error' not in request.GET:
                save_session_keys(request)
                return redirect(get_auth_url())
            if 'code' in request.GET:
                drive = create_service(request)
                write_export_data(request, context, si)
                
                fileTitle = context['tx_type'] + ' Report By Item ' + context['startDate'] + " to " + context['endDate'] + '.csv'
                upload_to_gdrive(fileTitle, drive, si)
            delete_session_keys(request)
            return render(request, 'inventory/reports/generate_report.html', context)

        # If Group by Item selected when clicking 'Generate'
        if 'itemizedOutput' in request.POST:
            context['itemizedOutput'] = request.POST['itemizedOutput']
            collect_itemized_data(context)

        # If not exported, then simply re-render page with new info   
        if 'export_table' not in request.POST \
            and 'export_drive_table' not in request.POST \
            and 'export_drive_table' not in request.session:     
            context['results'] = getPagination(request, context['results'], DEFAULT_PAGINATION_SIZE)
            return render(request, 'inventory/reports/generate_report.html', context)

        # If checkout, checkin, or checkin group by item (Export to Device)
        if 'export_table' in request.POST:
            response = HttpResponse()

            if 'itemizedOutput' in request.POST:
                response['Content-Disposition'] = 'attachment; filename=' + context['tx_type'] + ' Report By Item ' + request.POST['start-date'] + " to " + request.POST['end-date'] + '.csv'
            else:
                response['Content-Disposition'] = 'attachment; filename=' + context['tx_type'] + ' Report ' + request.POST['start-date'] + " to " + request.POST['end-date'] + '.csv'

            return write_export_table_data(request, context, response)

        # If checkout, checkin, or checkin group by item (Export to GDrive)
        if 'export_drive_table' in request.POST \
            or 'export_drive_table' in request.session:

            si = io.StringIO()

            if 'code' not in request.GET \
                and 'error' not in request.GET:
                save_session_keys(request)
                return redirect(get_auth_url())
            if 'code' in request.GET:
                drive = create_service(request)
                write_export_table_data(request, context, si)

                if 'itemizedOutput' in request.POST or 'itemizedOutput' in request.session:
                    fileTitle = context['tx_type'] + ' Report By Item ' + context['startDate'] + " to " + context['endDate'] + '.csv'
                else:
                    fileTitle = context['tx_type'] + ' Report ' + context['startDate'] + " to " + context['endDate'] + '.csv'

                upload_to_gdrive(fileTitle, drive, si)
            delete_session_keys(request)
            return render(request, 'inventory/reports/generate_report.html', context)

    # Generate w/ no Group By Item, then render
    today = date.today()
    weekAgo = today - timedelta(days=7)
    context['endDate'] = today.strftime('%Y-%m-%d')
    context['startDate'] = weekAgo.strftime('%Y-%m-%d')
    return render(request, 'inventory/reports/generate_report.html', context)

# Collects itemized data upon report generation if grouped by item
def collect_itemized_data(context):
    newUniqueItems = {}
    for res in context['results']: 
        for tx in res.items.all(): 
            item_key = (tx.item.id, tx.is_new)
            item_price = None
            if tx.is_new and tx.item.new_price != None:
                item_price = tx.item.new_price
            elif not tx.is_new and tx.item.used_price != None:
                item_price = tx.item.used_price
            if item_key not in newUniqueItems:
                newUniqueItems[item_key] = {
                    'id': tx.item.id,
                    'item': tx.item.name,
                    'category': "No category" if tx.item.category is None else tx.item.category.name,
                    'is_new': tx.is_new,
                    'quantity': tx.quantity,
                    'new_price': tx.item.new_price,
                    'used_price': tx.item.used_price,
                    'value': 0 if item_price is None else tx.quantity*item_price,
                    'tx_notes': res.notes_description()
                }
            else: 
                newUniqueItems[item_key]['quantity'] += tx.quantity
                newUniqueItems[item_key]['value'] += 0 if item_price is None else tx.quantity*item_price

                currNotes = newUniqueItems[item_key]['tx_notes']
                if res.notes and currNotes and str(res.id) not in currNotes: 
                    currNotes = currNotes + "<br>" + res.notes_description()
                    newUniqueItems[item_key]['tx_notes'] = currNotes

                currNotes = newUniqueItems[item_key]['tx_notes']
                if res.notes and currNotes and str(res.id) not in currNotes: 
                    currNotes = currNotes + "<br>" + res.notes_description()
                    newUniqueItems[item_key]['tx_notes'] = currNotes
                
    context['results'] = list(sorted(newUniqueItems.values(), key=lambda x: (x['item'], "New" if x['is_new'] else "Used")))

# Writes data for checkout, checkin, and checkin group by item
def write_export_table_data(request, context, csvObj):
    qs = context['results']
    writer = csv.writer(csvObj)

    if 'itemizedOutput' in request.POST or 'itemizedOutput' in request.session:
        if len(context.get('results', [])) != 0:
            totalPrice = 0
            headers = list(context['results'][0].keys())
            headers = [x for x in headers if x not in ['tx_notes', 'new_price', 'used_price']]
            headers.append('new/used price')
            writer.writerow(headers)
            for i in context['results']:
                row = []
                for h in headers:
                    if h == "new/used price":
                        if i['is_new']:
                            row.append(i['new_price'])
                        else:
                            row.append(i['used_price'])
                    else:
                        row.append(i[h])
                        if h == 'value':
                            totalPrice += i[h]
                writer.writerow(row)
            writer.writerow([])
            writer.writerow(["Total Value:", "", "", "", "", str(totalPrice)])
        return csvObj

    if len(qs) != 0:
        field_names = [f.name for f in qs.model._meta.get_fields()] + ["value"]
        totalPrice = 0
        writer.writerow(field_names)
        for i in qs:
            row = []
            for f in field_names:
                if f == "items":
                    txs = ', '.join([str(tx) for tx in i.items.all()])
                    row.append(txs)
                elif f == "value":
                    row.append(i.getValue())
                    totalPrice += i.getValue()
                else:
                    row.append(getattr(i, f))
            writer.writerow(row)
        writer.writerow([])
        if context["tx_type"] == "Checkout":
            writer.writerow(["Total Value:", "", "", "", "", "", "", "", str(totalPrice)])
        else:
            print("here")
            writer.writerow(["Total Value:", "", "", "", "", str(totalPrice)])
    return csvObj

# Writes data for checkout group by item
def write_export_data(request, context, csvObj):
    endDatetime = datetime.strptime('{} 23:59:59'.format(context['endDate']), '%Y-%m-%d %H:%M:%S')
    qs = Checkout.objects.filter(datetime__gte=context['startDate']).filter(datetime__lte=endDatetime).all()
    writer = csv.writer(csvObj)

    if qs is not None:
        writer.writerow(["item", "new/used", "category", "quantity", "new/used price", "total value"])

        uniqueItems = {} 

        for c in qs:
            for tx in c.items.all():
                item_key = (tx.item.id, tx.is_new)
                try: 
                    originalPrice = tx.item.new_price if tx.is_new else tx.item.used_price
                    adjustedPrice = float(request.POST.get(str(tx.item.id) + '-' + str(tx.is_new) + '-adjustment', originalPrice))
                except (ValueError, TypeError) as _: # noqa: F841
                    adjustedPrice = 0

                if item_key not in uniqueItems: 
                    uniqueItems[item_key] = [
                        tx.item.name,
                        "New" if tx.is_new else "Used",
                        "No category" if tx.item.category is None else tx.item.category.name,
                        tx.quantity,
                        adjustedPrice,
                        0 if adjustedPrice is None else round(tx.quantity*adjustedPrice, 2)
                    ]
                else: 
                    item_key = (tx.item.id, tx.is_new)
                    uniqueItems[item_key][3] += tx.quantity
                    uniqueItems[item_key][5] += 0 if adjustedPrice is None else tx.quantity*adjustedPrice
                    round(uniqueItems[item_key][5], 2)
        totalPrice = 0
        for item in uniqueItems.values():
            totalPrice = totalPrice + item[5]
        sorted_items = list(sorted(uniqueItems.values(), key=lambda x: (x[0], x[1])))
        for item in sorted_items:
            writer.writerow(item)
        writer.writerow([])
        writer.writerow(["Total Value:", "", "", "", "", str(totalPrice)])

    return csvObj

# Sets the context variables when a request from Google Auth is received
def set_context_vars_get(request, context):
    context['endDate'] = request.session['end-date']
    context['startDate'] = request.session['start-date']
    context['tx'] = request.session['tx-type']

    endDatetime = datetime.strptime('{} 23:59:59'.format(context['endDate']), '%Y-%m-%d %H:%M:%S')
    if request.session['tx-type'] == 'Checkin':
        context['results'] = Checkin.objects.filter(datetime__gte=context['startDate']).filter(datetime__lte=endDatetime).all()
    else:
        context['results'] = Checkout.objects.filter(datetime__gte=context['startDate']).filter(datetime__lte=endDatetime).all()
    
    context['tx_type'] = request.session['tx-type']

    context['totalValue'] = 0 
    for result in context['results']:
        context['totalValue'] = result.getValue() + context['totalValue']
    
    if 'itemizedOutput' in request.session:
        context['itemizedOutput'] = request.session['itemizedOutput']
        collect_itemized_data(context)

# Sets the context variables in any other case but Google Auth requests
def set_context_vars_post(request, context):
    context['endDate'] = request.POST['end-date']
    context['startDate'] = request.POST['start-date']
    context['tx'] = request.POST['tx-type']

    endDatetime = datetime.strptime('{} 23:59:59'.format(context['endDate']), '%Y-%m-%d %H:%M:%S')

    if request.POST['tx-type'] == 'Checkin':
        context['results'] = Checkin.objects.filter(datetime__gte=context['startDate']).filter(datetime__lte=endDatetime).all()
    else:
        context['results'] = Checkout.objects.filter(datetime__gte=context['startDate']).filter(datetime__lte=endDatetime).all()
    context['tx_type'] = request.POST['tx-type']

    if 'itemizedOutput' in request.POST:
        context['itemizedOutput'] = request.POST['itemizedOutput']

    context['totalValue'] = 0 
    for result in context['results']:
        context['totalValue'] = result.getValue() + context['totalValue']

# Saves request.POST vars as session keys for Google Auth redirect
def save_session_keys(request):
    if 'end-date' in request.POST:
        request.session['end-date'] = request.POST['end-date']
    if 'start-date' in request.POST:
        request.session['start-date'] = request.POST['start-date']
    if 'tx-type' in request.POST:
        request.session['tx-type'] = request.POST['tx-type']
    if 'export_drive' in request.POST:
        request.session['export_drive'] = request.POST['export_drive']
    if 'export_drive_table' in request.POST:
        request.session['export_drive_table'] = request.POST['export_drive_table']
    if 'itemizedOutput' in request.POST:
        request.session['itemizedOutput'] = request.POST['itemizedOutput']

# Deletes session keys when Google Auth request is finished being handled
def delete_session_keys(request):
    try:
        del request.session['end-date']
        del request.session['start-date']
        del request.session['tx-type']
        if 'export_drive' in request.session:
            del request.session['export_drive']
        if 'export_drive_table' in request.session:
            del request.session['export_drive_table']
        if 'itemizedOutput' in request.session:
            del request.session['itemizedOutput']
        if 'results' in request.session:
            del request.session['results']
    except KeyError:
        pass

# Refreshes session keys so old variables do not affect new reports
def refresh_session_keys(request):
    if ('export_drive_table' in request.session \
        or 'export_drive' in request.session) \
        and 'code' not in request.GET \
        and 'error' not in request.GET:
        
        delete_session_keys(request)

######################### ANALYTICS #########################

# Handles analytics page
    """ Loads the analytics page and has helper functions that query the type of item/category
    for each product. Rendered analytics page.

    Raises:
        Exception: None

    Returns:
        _type_: context and generated webpage
    """
@login_required(login_url='login')
def analytics(request):
    context = {}

    all_checkouts = Checkout.objects

    ###  Item Checkout Quantities tables
    one_week_ago = date.today() - timedelta(days=7)
    context['one_week_ago'] = one_week_ago
    one_month_ago = date.today() - relativedelta(months=1)
    context['one_month_ago'] = one_month_ago
    six_months_ago = date.today() - relativedelta(months=6)
    context['six_months_ago'] = six_months_ago
    context['all_time'] = 'All Time'

    def item_checkout_quantities(checkout_objects, date_gte, group_by):
        '''
        Generate checkout quantities as tuples of what's being grouped by and 
        quantity for all dates greater than or equal to date_gte (e.g. from one week ago).
        group_by should be either "item" or "category".
        '''
        if group_by not in {'item', 'category'}:
            raise Exception("Invalid group by: must be item or category")
        filtered_checkouts = checkout_objects.filter(datetime__date__gte=date_gte).all()

        # Get checkouts grouped by group_by, sorted by quantity checked out
        checkout_quantities = defaultdict(int)
        for checkout in filtered_checkouts:
            for itemTransaction in checkout.items.all():
                if group_by == 'item':
                    group_by_obj = itemTransaction.item
                else: # category
                    group_by_obj = itemTransaction.item.category

                quantity = itemTransaction.quantity
                checkout_quantities[group_by_obj] += quantity
        
        return checkout_quantities.items()

    item_quant_week = item_checkout_quantities(all_checkouts, one_week_ago, 'item')
    item_quant_month = item_checkout_quantities(all_checkouts, one_month_ago, 'item')
    item_quant_six_months = item_checkout_quantities(all_checkouts, six_months_ago, 'item')
    item_quant_all_time = item_checkout_quantities(all_checkouts, datetime.min, 'item')

    cat_quant_week = item_checkout_quantities(all_checkouts, one_week_ago, 'category')
    cat_quant_month = item_checkout_quantities(all_checkouts, one_month_ago, 'category')
    cat_quant_six_months = item_checkout_quantities(all_checkouts, six_months_ago, 'category')
    cat_quant_all_time = item_checkout_quantities(all_checkouts, datetime.min, 'category')

    ### Sorting columns for checkout quantities tables when pressed

    def new_sort_type():
        '''
        Returns new sort type based on a column, switching the sorting order each time. 
        The default sorting is "desc" for descending.
        '''
        # non_default instead of default b/c we always use "not" on sort_type
        non_default_sorting = "asc"
        sort_type = request.GET.get('sort_type', non_default_sorting)
        # switch sort_type
        new_sort_type = "asc" if sort_type == "desc" else "desc"
        
        return new_sort_type

    context['sort_type'] = new_sort_type()
    sort_reverse = context['sort_type'] == "desc"

    def order_function():
        '''
        Returns function with order field to sort by. Defaulted to 'checkout_quantity'.
        '''
        default_order = 'checkout_quantity'
        order_field = request.GET.get('order_by', default_order)

        order_lambda = lambda i_quantity: i_quantity[1] # default_order is checkout quantity
        if order_field == 'quantity':
            order_lambda = lambda i_quantity: i_quantity[0].quantity
        elif order_field == 'name':
            order_lambda = lambda i_quantity: i_quantity[0].name.lower()
        return order_lambda

    order_by_field = order_function()
    def sort_checkouts_paginated(item_quantities, order_func=order_by_field, sort_rev=sort_reverse):
        '''
        Sort the objects based on an order function and whether to reverse sort it.
        Return a paginated object of the sorted items and quantities.
        '''
        sorted_item_quants = sorted(item_quantities, key=order_func, reverse=sort_rev)
        return getPagination(request, sorted_item_quants, DEFAULT_PAGINATION_SIZE)

    context['item_week_checkouts'] = sort_checkouts_paginated(item_quant_week)
    context['item_month_checkouts'] = sort_checkouts_paginated(item_quant_month)
    context['item_six_month_checkouts'] = sort_checkouts_paginated(item_quant_six_months)
    context['item_all_time_checkouts'] = sort_checkouts_paginated(item_quant_all_time)

    context['cat_week_checkouts'] = sort_checkouts_paginated(cat_quant_week)
    context['cat_month_checkouts'] = sort_checkouts_paginated(cat_quant_month)
    context['cat_six_month_checkouts'] = sort_checkouts_paginated(cat_quant_six_months)
    context['cat_all_time_checkouts'] = sort_checkouts_paginated(cat_quant_all_time)

    context['LOW_QUANTITY_THRESHOLD'] = LOW_QUANTITY_THRESHOLD

    ###  Data for charts
    def chart_info_by_month(objects, count_field):
        '''
        Returns a tuple of chart's labels and data both as json-lists based on the objects grouped by year/month. 
        A label is a year + month as a string and data is an integer value for how many occurred in that month.
        count_field is the field in Checkout to count for each month.
        '''
        by_month = objects.annotate(   
            month=ExtractMonth('datetime'),
            year=ExtractYear('datetime') 
        ).values('year', 'month').annotate(
            count=Count(count_field, distinct=True)
        ).order_by('year', 'month')

        # Note: technically if a month has no checkouts, it will not show up as 0, 
        # but instead be omitted, but hoping that's not something that might happen for now
        labels_by_month, data_by_month = [], []
        for month_count in by_month:
            month = calendar.month_name[month_count['month']]
            labels_by_month.append(month + ' ' + str(month_count['year']))
            data_by_month.append(month_count['count'])
        
        return (json.dumps(labels_by_month), json.dumps(data_by_month))

    context['labels_couts'], context['data_couts'] = chart_info_by_month(all_checkouts, 'id')
    context['labels_fams'], context['data_fams'] = chart_info_by_month(all_checkouts, 'family')

    return render(request, 'inventory/analytics/analytics.html', context)

###################### CHECKIN/CHECKOUT VIEWS ######################

# Remove item from cart
def removeitem_action(request, index, location):
    saved_list = request.session['transactions-' + location]

    saved_list.pop(index)
    request.session['transactions-' + location] = saved_list

    return redirect(reverse('Check' + location))

# Edit Quantity in Checkout/in Dropdown
def editquantity_action(request, index, location, qty):
    saved_list = request.session['transactions-' + location]
    curr_item = json.loads(saved_list[index])
    if (int(qty) >= 1):
        curr_item[0]['fields']['quantity'] = qty
    else:
        curr_item[0]['fields']['quantity'] = 1

    saved_list[index] = json.dumps(curr_item)
    request.session['transactions-' + location] = saved_list

    return redirect(reverse('Check' + location))  

# Edit Used/New Status in Checkout/in Dropdown
def editisnew_action(request, index, location, isnew):
    saved_list = request.session['transactions-' + location]
    curr_item = json.loads(saved_list[index])
    if (isnew == 1):
        curr_item[0]['fields']['is_new'] = True
    else:
        curr_item[0]['fields']['is_new'] = False

    saved_list[index] = json.dumps(curr_item)
    request.session['transactions-' + location] = saved_list

    return redirect(reverse('Check' + location))  

# Create Family View 
@login_required
def createFamily_action(request, location):
    context = {}

    context['location'] = location

    if request.method == 'GET':
        context['form'] = CreateFamilyForm()
        
        return render(request, 'inventory/families/create.html', context)

    if request.method == 'POST':
        form = CreateFamilyForm(request.POST)

        context['form'] = form

        if not form.is_valid():
            return render(request, 'inventory/families/create.html', context)

        # category = form.cleaned_data['category']
        fname = form.cleaned_data['first_name']
        lname = form.cleaned_data['last_name']
        phone = form.cleaned_data['phone']

        family = Family(fname=fname, lname=lname, phone=phone)
        family.save()

        request.session['createdFamily'] = family.displayName
        messages.success(request, 'Family created')

        return redirect(reverse(location))

# Create Item View
@user_passes_test(lambda u: u.is_superuser)
def createItem_action(request, location):
    context = {}

    context['location'] = location

    if request.method == 'GET':
        context['form'] = CreateItemForm()
        
        return render(request, 'inventory/items/create.html', context)

    if request.method == 'POST':
        form = CreateItemForm(request.POST)

        context['form'] = form

        if not form.is_valid():
            return render(request, 'inventory/items/create.html', context)

        category = form.cleaned_data['category']
        name = form.cleaned_data['name']
        new_price = form.cleaned_data['new_price']
        used_price = form.cleaned_data['used_price']
        quantity = form.cleaned_data['quantity']

        item = Item(category=category, name=name, new_price=new_price, used_price=used_price, quantity=quantity)
        item.save()

        if location == 'in' or location == 'out':
            request.session["itemInfo"] = (item.name, item.quantity)
            messages.success(request, 'Item created')
            return redirect(reverse('Check' + location))
        else:
            return redirect(reverse(location))

# Checkin view
@login_required
def checkin_action(request):
    context = {}
        
    context['items'] = Item.objects.all()
    context['categories'] = Category.objects.all()

    # Create transactions if they don't exist
    if not 'transactions-in' in request.session or not request.session['transactions-in']:
        request.session['transactions-in'] = []

    # Deserialize transactions 
    serialized_transactions = request.session['transactions-in']
    transactions = []
    for tx in serialized_transactions:
        for deserialized_transaction in serializers.deserialize("json", tx):
            transactions.append(deserialized_transaction.object)

    context['transactions'] = transactions
    
    if request.method == 'GET':
        addItemForm = AddItemForm()
        #If a new item has been created on the check-in page, 
        #then once item has been created, fill out the checkin box with item info
        if ('itemInfo' in request.session):
            itemInfo = request.session['itemInfo']
            addItemForm.fields['item'].initial = itemInfo[0]
            addItemForm.fields['new_quantity'].initial = itemInfo[1]
            addItemForm.fields['used_quantity'].initial = 0
            del request.session['itemInfo']

        context['formadditem'] = addItemForm
        return render(request, 'inventory/checkin.html', context)

    if request.method == 'POST' and 'additem' in request.POST:
        form = AddItemForm(request.POST)

        context['formadditem'] = form

        # if item added to cart incorrectly, return to checkin page
        if not form.is_valid():
            return render(request, 'inventory/checkin.html', context)

        name = form.cleaned_data['item']
        new_quantity = form.cleaned_data['new_quantity']
        used_quantity = form.cleaned_data['used_quantity']

        item = Item.objects.filter(name=name).first()
    
        # pull up previous items in cart or create new cart
        if not 'transactions-in' in request.session or not request.session['transactions-in']:
            saved_list = []
        else:
            saved_list = request.session['transactions-in']

        # add new items to cart--if both new and used of same item type are being 
        # checked out, add as two separate items
        if used_quantity is not None:
            used_tx = serializers.serialize("json", [ ItemTransaction(item=item, quantity=used_quantity, is_new=False, ), ])
            saved_list.append(used_tx)

        if new_quantity is not None:
            new_tx = serializers.serialize("json", [ ItemTransaction(item=item, quantity=new_quantity, is_new=True, ), ])
            saved_list.append(new_tx)

        request.session['transactions-in'] = saved_list

        return redirect(reverse('Checkin'))

    if request.method == 'POST' and 'checkin' in request.POST:
        if not transactions:
            messages.warning(request, 'Could not create checkin: No items added')
            return render(request, 'inventory/checkin.html', context, status=400)

        # create checkin, adding notes if needed
        if 'checkin_notes' in request.POST and len(request.POST['checkin_notes']) > 0: 
            checkin = Checkin(user=request.user, notes=request.POST['checkin_notes'])
        else: 
            checkin = Checkin(user=request.user)
        checkin.save()

        # add all transactions to checkin, if multiple of same item, do not make multiple copies
        for tx in transactions:
            tx.save()

            checkin.items.add(tx)

            tx.item.quantity += tx.quantity
            tx.item.save()

        del request.session['transactions-in']
        request.session.modified = True

        messages.success(request, 'Checkin created.')
        return redirect(reverse('Checkin'))

# Checkout view
@login_required
def checkout_action(request):
    context = {}
    context['items'] = Item.objects.all()
    context['categories'] = Category.objects.all()
    context['createdFamily'] = 'no family'

    # Create transactions if they don't exist
    if not 'transactions-out' in request.session or not request.session['transactions-out']:
        request.session['transactions-out'] = []

    # Deserialize transactions 
    serialized_transactions = request.session['transactions-out']
    transactions = []
    for tx in serialized_transactions:
        for deserialized_transaction in serializers.deserialize("json", tx):
            transactions.append(deserialized_transaction.object)

    context['transactions'] = transactions

    if request.method == 'GET':
        addItemForm = AddItemForm()
        context['formadditem'] = addItemForm
        form = CheckOutForm()
        context['formcheckout'] = form

        # if new family was created, make the cart be of new family
        if ('createdFamily' in request.session):
            famName = request.session['createdFamily']
            form.fields['family'].initial = famName
            context['createdFamily'] = famName
            del request.session['createdFamily']

        # if new item was created, add the new item to the add to cart fields
        if ('itemInfo' in request.session):
            itemInfo = request.session['itemInfo']
            addItemForm.fields['item'].initial = itemInfo[0]
            addItemForm.fields['new_quantity'].initial = itemInfo[1]
            addItemForm.fields['used_quantity'].initial = 0
            del request.session['itemInfo']

        return render(request, 'inventory/checkout.html', context)

    if request.method == 'POST' and 'additem' in request.POST:
        form = AddItemForm(request.POST)

        context['formadditem'] = form
        context['formcheckout'] = CheckOutForm()

        # go back to checkout page if item was added incorrectly
        if not form.is_valid():
            return render(request, 'inventory/checkout.html', context)

        name = form.cleaned_data['item']
        used_quantity = form.cleaned_data['used_quantity']
        new_quantity = form.cleaned_data['new_quantity']

        item = Item.objects.filter(name=name).first()

        # pull up previous cart items or create new cart
        if not 'transactions-out' in request.session or not request.session['transactions-out']:
            saved_list = []
        else:
            saved_list = request.session['transactions-out']

        # add new items to cart--if both new and used of same item type are 
        # being checked out, add as two separate items
        if used_quantity is not None:
            used_tx = serializers.serialize("json", [ ItemTransaction(item=item, quantity=used_quantity, is_new=False, ), ])
            saved_list.append(used_tx)

        if new_quantity is not None:
            new_tx = serializers.serialize("json", [ ItemTransaction(item=item, quantity=new_quantity, is_new=True, ), ])
            saved_list.append(new_tx)

        request.session['transactions-out'] = saved_list

        return redirect(reverse('Checkout'))

    if request.method == 'POST' and 'checkout' in request.POST:
        form = CheckOutForm(request.POST)

        context['formcheckout'] = form
        context['formadditem'] = AddItemForm()

        if not form.is_valid():
            return render(request, 'inventory/checkout.html', context, status=400)

        family = form.cleaned_data['family'].strip()
        childName = form.cleaned_data['child'].strip()
        ageRange = form.cleaned_data['age']

        family_object = Family.objects.filter(displayName__exact=family)

        # if no items in cart, return 400 error
        if not transactions:
            messages.warning(request, 'Could not create checkout: No items added')
            return render(request, 'inventory/checkout.html', context, status=400)

        # add notes to checkout object if necessary
        notes = None
        if 'checkout_notes' in request.POST and request.POST['checkout_notes'] != '': 
            notes = request.POST['checkout_notes']
        
        checkout = Checkout(family=family_object[0], user=request.user, notes=notes, childName=childName, ageRange=ageRange)
        checkout.save()

        for tx in transactions:
            tx.save()

            checkout.items.add(tx)
            
            """ 
            Description: Hard stops the quantity left from ever being negative
            If the amount of items that are checked out are greater than the items available, the quantity_left is set to 0.
            """
            item_quantity_left = tx.item.quantity
            quantity_checked_out = tx.quantity
            if(item_quantity_left <= 0 or (item_quantity_left - quantity_checked_out <= 0)):
                tx.item.quantity = 0
            else:
                tx.item.quantity -= quantity_checked_out
            tx.item.save()
        
        del request.session['transactions-out']
        request.session.modified = True

        messages.success(request, 'Checkout created.')
        return redirect(reverse('Checkout'))

# Autocompletes item name 
def autocomplete_item(request):
    if 'term' in request.GET:
        qs = Item.objects.filter(name__icontains=request.GET.get('term'), outdated = False)
        names = list()
        for item in qs:
            names.append(item.name)
        return JsonResponse(names, safe=False)

# Autocompletes item name based on category
def autocomplete_item_category(request):
    if 'term' in request.GET:
        qs = Item.objects.filter(category__name__icontains=request.GET.get('term'), outdated = False)
        names = list()
        for item in qs:
            names.append(item.name)
        return JsonResponse(names, safe=False)

# Autocompletes family name   
def autocomplete_family(request):
    if 'term' in request.GET:
        qs = Family.objects.filter(Q(displayName__icontains=request.GET.get('term')) )
        names = list()
        for fam in qs: 
            names.append(fam.displayName)
        return JsonResponse(names, safe=False)
  
######################### DATABASE VIEWS #########################

# View family data
class FamilyIndexView(LoginRequiredMixin, SingleTableView):
    model = Family
    table_class = FamilyTable
    template_name = "inventory/families/index.html"

# View category data
class CategoryIndexView(LoginRequiredMixin, SingleTableView):
    model = Category
    table_class = CategoryTable
    template_name = "inventory/categories/index.html"

# View item data
class ItemIndexView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = Item
    table_class = ItemTable
    template_name = "inventory/items/index.html"
    filterset_class = ItemFilter

# View checkin data
class CheckinIndexView(LoginRequiredMixin, SingleTableView):
    model = Checkin
    table_class = CheckinTable
    template_name = "inventory/checkins/index.html"

# View checkout data
class CheckoutIndexView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = Checkout
    table_class = CheckoutTable
    template_name = "inventory/checkouts/index.html"
    filterset_class = CheckoutFilter


######################### VIEW HELPERS #########################

# Pagination handler
def getPagination(request, objects, count):
    page = request.POST.get('page', 1)
    paginator = Paginator(objects, count)
    
    try:
        paginationOut = paginator.page(page)
    except PageNotAnInteger:
        paginationOut = paginator.page(1)
    except EmptyPage:
        paginationOut = paginator.page(paginator.num_pages)
    return paginationOut





