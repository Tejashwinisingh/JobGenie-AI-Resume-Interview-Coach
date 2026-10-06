"""
apps/resumes/models.py

Resume model — stores metadata and the uploaded file for each user resume.
Actual file is stored under MEDIA_ROOT/resumes/<user_id>/<filename>.
"""
import os
from django.db import models
from django.conf import settings


def resume_upload_path(instance, filename):
    """Store resumes in a per-user subdirectory: resumes/<user_id>/<filename>."""
    return os.path.join('resumes', str(instance.user.id), filename)


class Resume(models.Model):
    """
    Stores a single resume upload.

    Fields:
        user            – the owning user (deletes cascade)
        original_filename – original name of the uploaded file (for display)
        file            – the stored file on disk
        file_type       – 'pdf' or 'docx'
        file_size       – size in bytes at upload time
        uploaded_at     – timestamp of the upload
    """

    FILE_TYPE_PDF  = 'pdf'
    FILE_TYPE_DOCX = 'docx'
    FILE_TYPE_CHOICES = [
        (FILE_TYPE_PDF,  'PDF'),
        (FILE_TYPE_DOCX, 'DOCX'),
    ]

    STATUS_PENDING    = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED  = 'completed'
    STATUS_FAILED     = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING,    'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED,  'Completed'),
        (STATUS_FAILED,     'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes',
    )
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=resume_upload_path)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveIntegerField(help_text='File size in bytes.')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Module 3 – Resume Processing Fields
    processing_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    raw_text = models.TextField(blank=True, null=True)
    cleaned_text = models.TextField(blank=True, null=True)
    processing_error = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'resumes'
        ordering = ['-uploaded_at']
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'

    def __str__(self):
        return f'{self.user.email} — {self.original_filename}'

    def delete(self, *args, **kwargs):
        """Remove the physical file from disk when the record is deleted."""
        storage = self.file.storage
        path = self.file.name
        super().delete(*args, **kwargs)
        if path and storage.exists(path):
            storage.delete(path)


class ParsedResume(models.Model):
    """
    Module 4 – Stores structured parsed data extracted from a Resume.
    """

    resume = models.OneToOneField(
        Resume,
        on_delete=models.CASCADE,
        related_name='parsed_data',
    )
    name = models.CharField(max_length=255, blank=True, default='')
    email = models.CharField(max_length=255, blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    linkedin = models.CharField(max_length=255, blank=True, default='')
    github = models.CharField(max_length=255, blank=True, default='')

    skills = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)

    parsed_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'resumes'
        verbose_name = 'Parsed Resume Data'
        verbose_name_plural = 'Parsed Resume Data'

    def __str__(self):
        return f'Parsed data for Resume #{self.resume_id} ({self.name or self.email or "Unnamed"})'

