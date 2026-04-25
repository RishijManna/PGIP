from django.contrib import admin

from .models import Document, Exam, JobOpportunity, Scheme, Task, UserProfile


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


admin.site.register(Task)
admin.site.register(Document)
admin.site.register(UserProfile)
