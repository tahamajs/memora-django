from django.contrib import admin
from .models import Board, Column, Card

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']

@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'board', 'order']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['note', 'column', 'priority', 'due_date']
