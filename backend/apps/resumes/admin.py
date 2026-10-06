"""
apps/resumes/admin.py
Django Admin registration for the Resume model.
"""
from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_filename', 'file_type', 'file_size_display', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('user__email', 'original_filename')
    readonly_fields = ('uploaded_at', 'file_size', 'file_type', 'original_filename')
    ordering = ('-uploaded_at',)

    def file_size_display(self, obj):
        return f'{round(obj.file_size / 1024, 1)} KB'
    file_size_display.short_description = 'File Size'
