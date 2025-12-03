from django.contrib import admin

from .models import BusinessProfile, Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status', 'owner', 'created_at')
    search_fields = ('name', 'email')
    list_filter = ('status', 'created_at')


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'public_id', 'notification_email')
    search_fields = ('business_name', 'public_id')
