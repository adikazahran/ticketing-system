# tickets/admin.py
from django.contrib import admin
from .models import Ticket, Comment, TicketActivity

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'assigned_to', 'created_by', 'created_at')
    list_filter = ('status', 'priority', 'assigned_to', 'created_by')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    raw_id_fields = ('assigned_to', 'created_by')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'created_at', 'content')
    list_filter = ('author', 'created_at')
    search_fields = ('content',)

@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'actor', 'action', 'timestamp')
    list_filter = ('action', 'timestamp', 'actor')
    search_fields = ('action',)
    readonly_fields = ('ticket', 'actor', 'action', 'timestamp') # Ini harusnya dibuat otomatis