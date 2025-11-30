from django.contrib import admin
from .models import Book, QRCode


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'publication_date', 'created_at']
    list_filter = ['created_at', 'publication_date']
    search_fields = ['title', 'author', 'isbn']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['book', 'created_at']
    readonly_fields = ['id', 'created_at']
    search_fields = ['book__title', 'book__author']
