from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.html import escape
from django.utils.dateparse import parse_date
from django.core.mail import send_mail
from django.http import JsonResponse
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from datetime import datetime
from calendar import monthrange
import random
import json
from .forms import UserForm, UserProfileForm
from .models import UserProfile
from .models import OTP, Task, Exam, Scheme, Document, JobOpportunity
from .forms import EmailForm, OTPForm, TaskForm, DocumentForm
from django.contrib import messages

# Dummy data for jobs and schemes
DUMMY_SCHEMES = [f"Scheme {i}" for i in range(1,83)]
DUMMY_JOBS = [f"Job {i}" for i in range(1,51)]
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_SENDS_PER_HOUR = 5
OTP_MAX_VERIFY_ATTEMPTS = 5
OTP_WINDOW_SECONDS = 60 * 60

def clear_personalization_state(request):
    for key in [
        "ai_assistant_history",
        "ai_recommendations",
        "ai_profile_snapshot",
    ]:
        request.session.pop(key, None)


def session_window(request, key):
    now = timezone.now().timestamp()
    window = request.session.get(key, {"started_at": now, "count": 0})

    if now - float(window.get("started_at", now)) > OTP_WINDOW_SECONDS:
        window = {"started_at": now, "count": 0}

    return window


def increment_session_window(request, key):
    window = session_window(request, key)
    window["count"] = int(window.get("count", 0)) + 1
    request.session[key] = window
    request.session.modified = True
    return window


def can_send_otp(request):
    now = timezone.now().timestamp()
    last_sent_at = request.session.get("otp_last_sent_at")

    if last_sent_at and now - float(last_sent_at) < OTP_RESEND_COOLDOWN_SECONDS:
        return False, "Please wait before requesting another OTP."

    window = session_window(request, "otp_send_window")
    if int(window.get("count", 0)) >= OTP_MAX_SENDS_PER_HOUR:
        return False, "Too many OTP requests. Please try again later."

    return True, ""


def record_otp_sent(request):
    request.session["otp_last_sent_at"] = timezone.now().timestamp()
    increment_session_window(request, "otp_send_window")


def reset_otp_session_state(request):
    for key in [
        "otp_last_sent_at",
        "otp_send_window",
        "otp_verify_window",
        "user_id",
    ]:
        request.session.pop(key, None)


def create_calendar_reminder(user, title, date):
    """
    Helper function to create calendar reminders
    """
    # Check if reminder already exists to avoid duplicates
    if not Task.objects.filter(user=user, title=title, date=date).exists():
        Task.objects.create(user=user, title=title, date=date)
        return True
    return False


def suggested_document_categories(profile, documents):
    uploaded = {str(doc.category or "").lower() for doc in documents}
    suggestions = []

    checks = [
        ("10th Marksheet", profile.class_10_percentage),
        ("12th Marksheet", profile.class_12_percentage),
        ("Degree/Certificate", profile.education in {"Undergraduate", "Postgraduate", "PhD"}),
        ("Income Certificate", profile.income),
        ("Caste Certificate", profile.caste and profile.caste != "General"),
        ("Resume", profile.skills),
    ]

    for category, needed in checks:
        if needed and category.lower() not in uploaded:
            suggestions.append(category)

    return suggestions

# Dashboard
def dashboard(request):
    schemes = Scheme.objects.all()
    exams = Exam.objects.all()
    jobs = JobOpportunity.objects.all()

    # Get filters from request
    exam_types = request.GET.getlist('exam_type')
    scheme_types = request.GET.getlist('scheme_type')
    locations = request.GET.getlist('location')
    categories = request.GET.getlist('category')
    modes = request.GET.getlist('mode')
    e_eligibilities = request.GET.getlist('e_eligibility')
    s_eligibilities = request.GET.getlist('s_eligibility')
    sort = request.GET.get('sort', 'date')

    # Apply filters to exams
    if exam_types:
        exams = exams.filter(exam_type__in=exam_types)
    if locations:
        exams = exams.filter(location__in=locations)
    if categories:
        exams = exams.filter(category__in=categories)
    if modes:
        exams = exams.filter(mode__in=modes)
    if e_eligibilities:
        exams = exams.filter(e_eligibility__in=e_eligibilities)

    # Apply filters to schemes
    if scheme_types:
        schemes = schemes.filter(scheme_type__in=scheme_types)
    if locations:
        schemes = schemes.filter(location__in=locations)
    if categories:
        schemes = schemes.filter(category__in=categories)
    if s_eligibilities:
        schemes = schemes.filter(s_eligibility__in=s_eligibilities)

    if locations:
        jobs = jobs.filter(location__in=locations)
    if categories:
        jobs = jobs.filter(sector__in=categories)

    # Apply sorting
    if sort == 'date':
        exams = exams.order_by('date')
        schemes = schemes.order_by('date')
        jobs = jobs.order_by(
            F('registration_end_date').asc(nulls_last=True),
            F('deadline').asc(nulls_last=True),
            'title',
        )
    elif sort == '-date':
        exams = exams.order_by('-date')
        schemes = schemes.order_by('-date')
        jobs = jobs.order_by(
            F('registration_end_date').desc(nulls_last=True),
            F('deadline').desc(nulls_last=True),
            'title',
        )
    elif sort == 'name':
        exams = exams.order_by('name')
        schemes = schemes.order_by('name')
        jobs = jobs.order_by('title')
    elif sort == '-name':
        exams = exams.order_by('-name')
        schemes = schemes.order_by('-name')
        jobs = jobs.order_by('-title')

    context = {
        'schemes': schemes,
        'exams': exams,
        'jobs': jobs,
    }
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'dashboard_content.html', context)
    
    return render(request, 'dashboard.html', context)

# Search Feature
def search_results(request):
    query = request.GET.get('q', '').strip()
    active_only = request.GET.get("active", "") == "1"
    deadline_from = request.GET.get("deadline_from", "")
    deadline_to = request.GET.get("deadline_to", "")
    deadline_from_date = parse_date(deadline_from) if deadline_from else None
    deadline_to_date = parse_date(deadline_to) if deadline_to else None

    if any([query, active_only, deadline_from, deadline_to]):
        request.session["saved_search_filters"] = {
            "q": query,
            "active": "1" if active_only else "",
            "deadline_from": deadline_from,
            "deadline_to": deadline_to,
        }

    exams = Exam.objects.none()
    schemes = Scheme.objects.none()
    jobs = JobOpportunity.objects.none()

    if query:
        exams = Exam.objects.filter(
            Q(name__icontains=query)
            | Q(category__icontains=query)
            | Q(location__icontains=query)
            | Q(conducting_body__icontains=query)
            | Q(required_skills__icontains=query)
            | Q(salary_package__icontains=query)
        )

        schemes = Scheme.objects.filter(
            Q(name__icontains=query)
            | Q(category__icontains=query)
            | Q(location__icontains=query)
            | Q(benefits__icontains=query)
            | Q(benefit_amount__icontains=query)
            | Q(required_documents__icontains=query)
        )

        jobs = JobOpportunity.objects.filter(
            Q(title__icontains=query)
            | Q(company_or_org__icontains=query)
            | Q(sector__icontains=query)
            | Q(required_skills__icontains=query)
            | Q(location__icontains=query)
        )

    today = timezone.localdate()
    if active_only:
        exams = exams.filter(Q(registration_end_date__gte=today) | Q(date__gte=today))
        schemes = schemes.filter(Q(registration_end_date__gte=today) | Q(date__gte=today))
        jobs = jobs.filter(Q(registration_end_date__gte=today) | Q(deadline__gte=today))

    if deadline_from_date:
        exams = exams.filter(Q(registration_end_date__gte=deadline_from_date) | Q(date__gte=deadline_from_date))
        schemes = schemes.filter(Q(registration_end_date__gte=deadline_from_date) | Q(date__gte=deadline_from_date))
        jobs = jobs.filter(Q(registration_end_date__gte=deadline_from_date) | Q(deadline__gte=deadline_from_date))

    if deadline_to_date:
        exams = exams.filter(Q(registration_end_date__lte=deadline_to_date) | Q(date__lte=deadline_to_date))
        schemes = schemes.filter(Q(registration_end_date__lte=deadline_to_date) | Q(date__lte=deadline_to_date))
        jobs = jobs.filter(Q(registration_end_date__lte=deadline_to_date) | Q(deadline__lte=deadline_to_date))

    exams = exams.distinct().order_by(F("registration_end_date").asc(nulls_last=True), F("date").asc(nulls_last=True), "name")
    schemes = schemes.distinct().order_by(F("registration_end_date").asc(nulls_last=True), F("date").asc(nulls_last=True), "name")
    jobs = jobs.distinct().order_by(F("registration_end_date").asc(nulls_last=True), F("deadline").asc(nulls_last=True), "title")

    exams_count = exams.count()
    schemes_count = schemes.count()
    jobs_count = jobs.count()
    page_number = request.GET.get("page")

    context = {
        'query': query,
        'exams': Paginator(exams, 12).get_page(page_number),
        'schemes': Paginator(schemes, 12).get_page(page_number),
        'jobs': Paginator(jobs, 12).get_page(page_number),
        'exams_count': exams_count,
        'schemes_count': schemes_count,
        'jobs_count': jobs_count,
        'active_only': active_only,
        'deadline_from': deadline_from,
        'deadline_to': deadline_to,
        'saved_filters': request.session.get("saved_search_filters", {}),
    }
    context["search_has_previous"] = (
        context["exams"].has_previous()
        or context["schemes"].has_previous()
        or context["jobs"].has_previous()
    )
    context["search_has_next"] = (
        context["exams"].has_next()
        or context["schemes"].has_next()
        or context["jobs"].has_next()
    )
    context["search_page_number"] = max(
        context["exams"].number,
        context["schemes"].number,
        context["jobs"].number,
    )
    context["search_previous_page_number"] = max(context["search_page_number"] - 1, 1)
    context["search_next_page_number"] = context["search_page_number"] + 1
    return render(request, 'search_results.html', context)

def demo_register(request, item_type, item_id):
    if item_type == "exam":
        item = get_object_or_404(Exam, id=item_id)
    else:
        item = get_object_or_404(Scheme, id=item_id)

    if request.method == "POST":
        return render(request, 'success.html', {
            'item_type': item_type,
            'item_name': item.name
        })

    return render(request, 'demo_register.html', {
        'item_type': item_type,
        'item': item
    })


def registration_success(request):
    return render(request, 'success.html')


def contact_view(request):
    return render(request, 'contact.html')

# Calendar Page
def calendar_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    today = datetime.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    month_days = monthrange(year, month)[1]

    tasks = Task.objects.filter(user=request.user, date__year=year, date__month=month)
    calendar_days = []

    for day in range(1, month_days + 1):
        current_date = datetime(year, month, day)
        is_sunday = current_date.weekday() == 6
        day_tasks = tasks.filter(date=current_date.date())
        calendar_days.append({
            'day': day,
            'date': current_date.date(),
            'tasks': day_tasks,
            'is_sunday': is_sunday,
        })

    if request.method == 'POST':
        if 'add' in request.POST:
            form = TaskForm(request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.user = request.user
                task.save()
                return redirect('calendar')
        elif 'delete' in request.POST:
            Task.objects.filter(
                id=request.POST.get('task_id'),
                user=request.user,
            ).delete()
            return redirect('calendar')
    else:
        form = TaskForm()

    context = {
        'calendar_days': calendar_days,
        'form': form,
        'year': year,
        'month': month,
    }
    return render(request, 'calendar.html', context)

# Login and OTP
def send_otp_email(user):
    otp = f"{random.randint(100000, 999999)}"
    OTP.objects.update_or_create(user=user, defaults={"otp_code": otp, "created_at": timezone.now()})
    send_mail(
        subject='Your OTP Code',
        message=f'Hi {user.username},\n\nYour OTP for login is: {otp}\n\nThis will expire in 10 minutes.',
        from_email='youremail@gmail.com',
        recipient_list=[user.email],
        fail_silently=False,
    )

def login_request(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            allowed, error = can_send_otp(request)
            if not allowed:
                form.add_error(None, error)
                return render(request, 'login.html', {'form': form})

            email = form.cleaned_data['email']
            user, _ = User.objects.get_or_create(username=email, email=email)
            send_otp_email(user)
            record_otp_sent(request)
            request.session['user_id'] = user.id
            return redirect('verify_otp')
    else:
        form = EmailForm()
    return render(request, 'login.html', {'form': form})


@require_POST
def resend_otp(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    allowed, error = can_send_otp(request)
    if not allowed:
        messages.error(request, error)
        return redirect("verify_otp")

    user = get_object_or_404(User, id=user_id)
    send_otp_email(user)
    record_otp_sent(request)
    messages.success(request, "A new OTP has been sent.")
    return redirect("verify_otp")

def verify_otp(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            attempts = session_window(request, "otp_verify_window")
            if int(attempts.get("count", 0)) >= OTP_MAX_VERIFY_ATTEMPTS:
                form.add_error(None, "Too many failed attempts. Please request a new OTP.")
                return render(request, 'otp.html', {'form': form})

            otp_input = form.cleaned_data['otp']
            try:
                otp_obj = OTP.objects.get(user=user)
                if otp_obj.otp_code == otp_input:
                    if otp_obj.is_expired():
                        form.add_error(None, "OTP has expired. Please login again.")
                    else:
                        login(request, user)
                        otp_obj.delete()
                        reset_otp_session_state(request)
                        return redirect('dashboard')
                else:
                    increment_session_window(request, "otp_verify_window")
                    form.add_error('otp', "Invalid OTP.")
            except OTP.DoesNotExist:
                form.add_error(None, "OTP not found. Please login again.")
    else:
        form = OTPForm()
    return render(request, 'otp.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


# API for FullCalendar (Reminders + Exams)
@login_required
def api_events(request):
    tasks = Task.objects.filter(user=request.user)
    exams = Exam.objects.all()
    schemes = Scheme.objects.all()
    jobs = JobOpportunity.objects.all()

    events = []

    # Reminders
    for t in tasks:
        events.append({
            "id": f"task-{t.id}",
            "title": f"📝 {t.title}",
            "start": t.date.strftime("%Y-%m-%d"),  # 👈 Correct format
            "allDay": True,
            "color": "#4D96FF",  # Blue reminders
            "type": "reminder",
        })

    # Exams
    for e in exams:
        if not e.date:
            continue

        events.append({
            "id": f"exam-{e.id}",
            "title": f"📚 {e.name}",
            "start": e.date.strftime("%Y-%m-%d"),
            "allDay": True,
            "color": "#FF6B6B",  # Red exams
            "url": f"/exam/{e.id}/",
            "type": "exam",
            "category": e.category,
            "location": e.location,
            "mode": e.mode,
            "e_eligibility": e.e_eligibility,
            "conducting_body": e.conducting_body,
            "application_fee": e.application_fee,
            "salary_package": e.salary_package,
            "registration_window": e.registration_window,
        })

    for scheme in schemes:
        if not scheme.date:
            continue

        events.append({
            "id": f"scheme-{scheme.id}",
            "title": f"Scheme: {scheme.name}",
            "start": scheme.date.strftime("%Y-%m-%d"),
            "allDay": True,
            "color": "#2FB344",
            "url": f"/details/scheme/{scheme.id}/",
            "type": "scheme",
            "category": scheme.category,
            "location": scheme.location,
            "s_eligibility": scheme.s_eligibility,
            "description": scheme.description,
            "benefits": scheme.benefits,
            "benefit_amount": scheme.benefit_amount,
            "required_documents": scheme.required_documents,
            "registration_window": scheme.registration_window,
        })

    for job in jobs:
        item_date = job.effective_deadline

        if not item_date:
            continue

        events.append({
            "id": f"job-{job.id}",
            "title": f"Opportunity: {job.title}",
            "start": item_date.strftime("%Y-%m-%d"),
            "allDay": True,
            "color": "#7C3AED",
            "url": f"/details/job/{job.id}/",
            "type": "job",
            "category": job.sector,
            "location": job.location,
            "description": job.description,
            "compensation": job.compensation_summary,
            "registration_window": job.registration_window,
            "source_name": job.source_name,
        })

    return JsonResponse(events, safe=False)

@login_required
@require_POST
def add_reminder(request):
    try:
        data = json.loads(request.body)
        title = str(data.get("title", "")).strip()
        date_str = data.get("date")
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"status": "error", "message": "Invalid reminder payload"}, status=400)

    if not title:
        return JsonResponse({"status": "error", "message": "Title is required"}, status=400)

    if Task.objects.filter(user=request.user, title=title, date=date).exists():
        return JsonResponse({"status": "duplicate", "message": "Reminder already exists"})

    Task.objects.create(user=request.user, title=title, date=date)
    return JsonResponse({"status": "success"})

@login_required
@require_http_methods(["DELETE"])
def delete_reminder(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        return JsonResponse({"error": "Reminder not found"}, status=404)

    task.delete()
    return JsonResponse({"status": "success"})


# ------------------ Document Uploads ------------------
@login_required
def documents(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            return redirect('documents')
    else:
        form = DocumentForm()

    docs = Document.objects.filter(user=request.user)
    return render(request, 'documents.html', {'form': form, 'documents': docs})

@login_required
def delete_document(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)
    if request.method == "POST":
        document.file.delete(save=False)  # delete file from storage
        document.delete()  # delete db record
        return redirect('profile')
    return redirect('profile')


# AJAX endpoints for exam and scheme details (can be removed if not used elsewhere)
@require_GET
def exam_detail(request, exam_id):
    try:
        exam = Exam.objects.get(id=exam_id)
        # Format the details in HTML with all available information
        details_html = f"""
        <div class="exam-details">
            <h4>{escape(exam.name)}</h4>
            <div class="details-section">
                <p><strong>Type:</strong> {escape(exam.exam_type)}</p>
                <p><strong>Category:</strong> {escape(exam.category)}</p>
                <p><strong>Location:</strong> {escape(exam.location)}</p>
                <p><strong>Mode:</strong> {escape(exam.mode)}</p>
                <p><strong>Date:</strong> {escape(exam.date)}</p>
                <p><strong>Eligibility:</strong> {escape(exam.e_eligibility)}</p>
            </div>
            <div class="additional-info">
                <h5>Additional Information</h5>
                <p>{escape(exam.additional_info)}</p>
            </div>
        </div>
        """
        return JsonResponse({
            'name': exam.name,
            'details': details_html
        })
    except Exam.DoesNotExist:
        return JsonResponse({'error': 'Exam not found'}, status=404)

@require_GET
def scheme_detail(request, scheme_id):
    try:
        scheme = Scheme.objects.get(id=scheme_id)
        # Format the details in HTML with all available information
        details_html = f"""
        <div class="scheme-details">
            <h4>{escape(scheme.name)}</h4>
            <div class="details-section">
                <p><strong>Type:</strong> {escape(scheme.scheme_type)}</p>
                <p><strong>Category:</strong> {escape(scheme.category)}</p>
                <p><strong>Location:</strong> {escape(scheme.location)}</p>
                <p><strong>Date:</strong> {escape(scheme.date)}</p>
                <p><strong>Eligibility:</strong> {escape(scheme.s_eligibility)}</p>
                <p><strong>Benefits:</strong> {escape(scheme.benefits)}</p>
                <p><strong>Description:</strong> {escape(scheme.description)}</p>
            </div>
            <div class="additional-info">
                <h5>Additional Information</h5>
                <p>{escape(scheme.additional_info)}</p>
            </div>
        </div>
        """
        return JsonResponse({
            'name': scheme.name,
            'details': details_html
        })
    except Scheme.DoesNotExist:
        return JsonResponse({'error': 'Scheme not found'}, status=404)

# Manual add to calendar view
@login_required
@require_POST
def add_to_calendar(request):
    item_type = request.POST.get('item_type')
    item_id = request.POST.get('item_id')

    if item_type == 'exam':
        item = get_object_or_404(Exam, id=item_id)
        title = f"Exam: {item.name}"
        item_date = item.date
        item_name = item.name
    elif item_type == 'job':
        item = get_object_or_404(JobOpportunity, id=item_id)
        title = f"Job: {item.title}"
        item_date = item.effective_deadline
        item_name = item.title
    elif item_type == 'scheme':
        item = get_object_or_404(Scheme, id=item_id)
        title = f"Scheme: {item.name}"
        item_date = item.date
        item_name = item.name
    else:
        messages.error(request, "Invalid calendar item type.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    if not item_date:
        messages.info(request, f"{item_name} has no listed date yet.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    created = create_calendar_reminder(request.user, title, item_date)
    if created:
        messages.success(request, f"Added {item_name} to your calendar!")
    else:
        messages.info(request, f"{item_name} is already in your calendar!")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

# ------------------ Profile + Documents ------------------
@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    documents = Document.objects.filter(user=request.user)
    user_form = UserForm(instance=request.user)
    profile_form = UserProfileForm(instance=profile)
    doc_form = DocumentForm()

    if request.method == "POST":
        # Profile update
        if "update_profile" in request.POST:
            user_form = UserForm(request.POST, instance=request.user)
            profile_form = UserProfileForm(request.POST, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile = profile_form.save()  # handles interests join()
                request.user.refresh_from_db()
                profile.refresh_from_db()
                clear_personalization_state(request)
                return redirect("profile")

        # Document upload
        elif "upload_document" in request.POST:
            doc_form = DocumentForm(request.POST, request.FILES)
            if doc_form.is_valid():
                d = doc_form.save(commit=False)
                d.user = request.user
                d.save()
                return redirect("profile")

    return render(request, "profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "doc_form": doc_form,
        "documents": documents,
        "suggested_documents": suggested_document_categories(profile, documents),
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services.ai_recommendation import (
    build_eligibility_explanation,
    recommend_exams,
    recommend_jobs,
    recommend_schemes,
)
from .services.ai_assistant import answer_question


@login_required
def recommendations_view(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    all_exams = Exam.objects.all()

    all_schemes = Scheme.objects.all()
    all_jobs = JobOpportunity.objects.all()

    recommended_exams = recommend_exams(
        profile,
        all_exams
    )

    recommended_schemes = recommend_schemes(
        profile,
        all_schemes
    )
    recommended_jobs = recommend_jobs(
        profile,
        all_jobs
    )

    for exam in recommended_exams:
        exam.ai_explanation = build_eligibility_explanation(
            profile,
            exam,
            "exam"
        )

    for scheme in recommended_schemes:
        scheme.ai_explanation = build_eligibility_explanation(
            profile,
            scheme,
            "scheme"
        )

    for job in recommended_jobs:
        job.ai_explanation = build_eligibility_explanation(
            profile,
            job,
            "job"
        )

    interests = []

    if profile.interests:

        interests = [
            i.strip()
            for i in profile.interests.split(",")
            if i.strip()
        ]

    context = {
        "exams": recommended_exams,
        "schemes": recommended_schemes,
        "jobs": recommended_jobs,
        "interests": interests,
        "user_location": profile.location,
    }

    return render(
        request,
        "recommendations.html",
        context
    )


@login_required
def ai_assistant_view(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    recommended_exams = recommend_exams(
        profile,
        Exam.objects.all()
    )[:3]
    recommended_schemes = recommend_schemes(
        profile,
        Scheme.objects.all()
    )[:3]
    recommended_jobs = recommend_jobs(
        profile,
        JobOpportunity.objects.all()
    )[:3]

    return render(
        request,
        "ai_assistant.html",
        {
            "recommended_exams": recommended_exams,
            "recommended_schemes": recommended_schemes,
            "recommended_jobs": recommended_jobs,
            "profile": profile,
        }
    )


@login_required
@require_POST
def ai_assistant_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON payload."},
            status=400
        )

    question = payload.get("message", "")
    history = payload.get("history", [])
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )
    request.user.refresh_from_db()
    profile.refresh_from_db()
    result = answer_question(
        profile,
        question,
        Exam.objects.all(),
        Scheme.objects.all(),
        JobOpportunity.objects.all(),
        history
    )

    return JsonResponse(result)

def details_view(request, item_type, item_id):
    if item_type == 'exam':
        item = get_object_or_404(Exam, id=item_id)
        display_name = item.name
        display_type = item.exam_type
        display_date = item.date
        display_eligibility = item.e_eligibility
    elif item_type == 'scheme':
        item = get_object_or_404(Scheme, id=item_id)
        display_name = item.name
        display_type = item.scheme_type
        display_date = item.date
        display_eligibility = item.s_eligibility
    elif item_type == 'job':
        item = get_object_or_404(JobOpportunity, id=item_id)
        display_name = item.title
        display_type = item.get_opportunity_type_display()
        display_date = item.effective_deadline
        display_eligibility = item.qualification
    else:
        # Handle invalid item_type
        return render(request, "error.html", {"message": "Invalid item type"})
    
    context = {
        "item_type": item_type,
        "item": item,  # Pass the actual object
        "item_id": item_id,
        "display_name": display_name,
        "display_type": display_type,
        "display_date": display_date,
        "display_eligibility": display_eligibility,
        "ai_explanation": build_eligibility_explanation(
            UserProfile.objects.get_or_create(user=request.user)[0]
            if request.user.is_authenticated
            else UserProfile(),
            item,
            item_type
        ),
    }
    return render(request, "details.html", context)
