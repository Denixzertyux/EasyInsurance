from django.contrib import admin
from .models import User, Insurance

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email')
    search_fields = ('username', 'email')

@admin.register(Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = ('insurance_id', 'car_brand', 'car_model', 'VIN', 'starting_date', 'expiry_date')
    search_fields = ('insurance_id', 'VIN', 'car_brand', 'car_model')
    list_filter = ('car_brand', 'starting_date', 'expiry_date')
