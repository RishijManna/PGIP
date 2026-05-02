from django.contrib import admin
from django.core.management import call_command

from .models import Document, Exam, JobOpportunity, Scheme, Task, UserProfile


@admin.action(description="Sync source-backed exams, schemes, and opportunities")
def sync_source_backed_records(modeladmin, request, queryset):
    call_command("sync_real_opportunities", verbosity=0)
    modeladmin.message_user(
        request,
        "Source-backed exams, schemes, and opportunities were synced.",
    )


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    search_fields = ["name", "category", "location", "conducting_body", "source_name"]
    list_filter = ["exam_type", "category", "location", "is_live_source"]
    list_display = [
        "name",
        "category",
        "exam_type",
        "location",
        "date",
        "registration_end_date",
        "source_name",
    ]
    actions = [sync_source_backed_records]


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    search_fields = ["name", "category", "location", "scheme_type", "source_name"]
    list_filter = ["scheme_type", "category", "location", "is_live_source"]
    list_display = [
        "name",
        "category",
        "scheme_type",
        "location",
        "registration_end_date",
        "source_name",
    ]
    actions = [sync_source_backed_records]


@admin.register(JobOpportunity)
class JobOpportunityAdmin(admin.ModelAdmin):
    search_fields = ["title", "company_or_org", "sector", "required_skills"]
    list_filter = ["opportunity_type", "sector", "location", "is_live_source"]
    list_display = [
        "title",
        "company_or_org",
        "opportunity_type",
        "location",
        "registration_start_date",
        "registration_end_date",
        "compensation_type",
        "source_name",
    ]
    actions = [sync_source_backed_records]


admin.site.register(Task)
admin.site.register(Document)
admin.site.register(UserProfile)
