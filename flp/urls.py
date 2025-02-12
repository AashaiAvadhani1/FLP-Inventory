"""flp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from inventory import views

urlpatterns = [
    # GENERIC ROUTES 
    path('admin/', admin.site.urls),
    path('', views.home, name="Home"),
    path('autocomplete_item/', views.autocomplete_item, name="autocomplete_item"),
    path('autocomplete_item_category/', views.autocomplete_item_category, name="autocomplete_item_category"),
    path('autocomplete_family/', views.autocomplete_family, name="autocomplete_family"),
    path('about/', views.about, name="About"),  
    path('PrivacyPolicy/', views.privacy_policy, name="PrivacyPolicy"),  

    # AUTH ROUTES 
    path('login/', views.login_action, name='Login'),
    path('logout/', views.logout_action, name='Logout'),

    # ACTION ROUTES
    path('report/', views.generate_report, name='Report'),
    path('checkin/', views.checkin_action, name='Checkin'),
    path('checkout/', views.checkout_action, name='Checkout'),
    path('createitem/<str:location>/', views.createItem_action, name='CreateItem'),
    path('createFamily/<str:location>/', views.createFamily_action, name='CreateFamily'),
    path('editquantity/<int:index>/<str:location>/<int:qty>/', views.editquantity_action, name='EditQuantity'),
    path('editisnew/<int:index>/<str:location>/<int:isnew>/', views.editisnew_action, name='EditIsNew'),
    path('removeitem/<int:index>/<str:location>/', views.removeitem_action, name='RemoveItem'),
    path('analytics/', views.analytics, name='Analytics'),

    path('families/index/', views.FamilyIndexView.as_view(), name="Families"),
    path('families/create/', views.createFamily_action, name='CreateFamily'),
    path('categories/index/', views.CategoryIndexView.as_view(), name="Categories"),
    path('items/index/', views.ItemIndexView.as_view(), name="Items"),
    path('items/create/<str:location>/', views.createItem_action, name='CreateItem'),
    path('checkins/index/', views.CheckinIndexView.as_view(), name="Checkins"),
    path('checkouts/index/', views.CheckoutIndexView.as_view(), name="Checkouts"),
]
