from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta


class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

#----------------- Stores reminders on dates----------------------------
class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    date = models.DateField()

    def __str__(self):
        return f"{self.title} on {self.date}"


# -------------------- EXAM MODEL --------------------
from django.db import models

class Exam(models.Model):
    EXAM_TYPE_CHOICES = [
        ('Government', 'Government'),
        ('Private', 'Private'),
        ('State Level', 'State Level'),
        ('National Level', 'National Level'),
        ('University Level', 'University Level'),
        ('Professional', 'Professional'),  # Added from seed_data
    ]

    LOCATION_CHOICES = [
        ('Delhi', 'Delhi'),
        ('Karnataka', 'Karnataka'),
        ('West Bengal', 'West Bengal'),
        ('Hyderabad', 'Hyderabad'),
        ('All India', 'All India'),
        ('Multiple Cities', 'Multiple Cities'),
        ('Maharashtra', 'Maharashtra'),
        ('Telangana', 'Telangana'),
        ('Andhra Pradesh', 'Andhra Pradesh'),
        ('Odisha', 'Odisha'),
        ('Gujarat', 'Gujarat'),
        ('Chhattisgarh', 'Chhattisgarh'),
        ('Madhya Pradesh', 'Madhya Pradesh'),
        ('Tamil Nadu', 'Tamil Nadu'),
        ('Uttarakhand', 'Uttarakhand'),
        ('Kerala', 'Kerala'),
        ('Ahmedabad', 'Ahmedabad'),
        ('Rural India', 'Rural India'),
        ('Coastal Cities', 'Coastal Cities'),  # Added from seed_data
    ]

    CATEGORY_CHOICES = [
        ('Engineering', 'Engineering'),
        ('Medical', 'Medical'),
        ('Banking', 'Banking'),
        ('Defense', 'Defense'),
        ('Civil Services', 'Civil Services'),
        ('Teaching', 'Teaching'),
        ('Law', 'Law'),
        ('Management', 'Management'),
        ('Science', 'Science'),
        ('Design', 'Design'),
        ('Employment', 'Employment'),
        ('Insurance', 'Insurance'),
        ('Food Corporation', 'Food Corporation'),
        ('Agriculture', 'Agriculture'),
        ('Hotel Management', 'Hotel Management'),
        ('Environment', 'Environment'),  # Added from seed_data
    ]

    MODE_CHOICES = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    ]

    # Choices for eligibility
    ELIGIBILITY_CHOICES = [
        ('10th Pass', '10th Pass'),
        ('12th Pass', '12th Pass'),
        ('Graduate', 'Graduate'),
        ('Post Graduate', 'Post Graduate'),
    ]

    # Fields
    name = models.CharField(max_length=255, unique=True)
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES, default="None")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="None")
    location = models.CharField(max_length=100, choices=LOCATION_CHOICES, default="None")
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="None")
    date = models.DateField(blank=True, null=True)
    e_eligibility = models.CharField(max_length=20, choices=ELIGIBILITY_CHOICES,default="None")
    additional_info = models.TextField(blank=True, null=True)
    conducting_body = models.CharField(max_length=160, blank=True)
    registration_start_date = models.DateField(blank=True, null=True)
    registration_end_date = models.DateField(blank=True, null=True)
    application_fee = models.CharField(max_length=180, blank=True)
    salary_package = models.CharField(max_length=180, blank=True)
    required_skills = models.TextField(blank=True)
    source_name = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(blank=True)
    official_notification_url = models.URLField(blank=True)
    application_url = models.URLField(blank=True)
    is_live_source = models.BooleanField(default=False)
    data_as_of = models.DateField(blank=True, null=True)
    verification_notes = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def effective_deadline(self):
        return self.registration_end_date or self.date

    @property
    def registration_window(self):
        if self.registration_start_date and self.registration_end_date:
            return f"{self.registration_start_date} to {self.registration_end_date}"

        if self.registration_end_date:
            return f"Last date: {self.registration_end_date}"

        if self.registration_start_date:
            return f"Opens: {self.registration_start_date}"

        return "Not listed"




# -------------------- SCHEME MODEL --------------------
class Scheme(models.Model): 
    SCHEME_TYPE_CHOICES = [ ('Central Government', 
                             'Central Government'), 
                           ('State Government', 'State Government'), 
                           ('Welfare', 'Welfare'), 
                           ('Scholarship', 'Scholarship'), 
                           ('Loan', 'Loan'), ('Employment', 'Employment'), 
                           ('Training', 'Training'),  ('Pension', 'Pension'),  ('Insurance', 'Insurance'),  ('Financial Assistance', 'Financial Assistance'),  ('Subsidy', 'Subsidy'),  ('Allowance', 'Allowance'),  ]

    SCHEME_ELIGIBILITY_CHOICES = [ ('10th Pass', '10th Pass'), ('12th Pass', '12th Pass'), ('Graduate', 'Graduate'), ('Postgraduate', 'Postgraduate'), ('Open to All', 'Open to All'), ('18+ years', '18+ years'),  ('18-50 years', '18-50 years'),  ('18-70 years', '18-70 years'),  ('18-40 years', '18-40 years'),  ('Senior Citizens', 'Senior Citizens'),  ('BPL Families', 'BPL Families'),  ('SC/ST/Women', 'SC/ST/Women'),  ('Rural Population', 'Rural Population'),  ('Farmers', 'Farmers'),  ('State Residents', 'State Residents'),  ('Girl Students', 'Girl Students'),  ('Girls from BPL families', 'Girls from BPL families'),  ('Graduate, Unemployed', 'Graduate, Unemployed'),  ('All Residents', 'All Residents'),  ('Startups registered in Delhi', 'Startups registered in Delhi'),  ('Low Income', 'Low Income'),  ]

    SCHEME_CATEGORY_CHOICES = [ ('Education', 'Education'), ('Employment', 'Employment'), ('Health', 'Health'), ('Finance', 'Finance'), ('General', 'General'), ('Entrepreneurship', 'Entrepreneurship'), ('Housing', 'Housing'),  ('Welfare', 'Welfare'),  ('Insurance', 'Insurance'),  ('Pension', 'Pension'),  ('Food Corporation', 'Food Corporation'),  ]

    SCHEME_LOCATION_CHOICES = [ ('Delhi', 'Delhi'),
                        ('Karnataka', 'Karnataka'),
                        ('West Bengal', 'West Bengal'), 
                        ('Hyderabad', 'Hyderabad'),
                        ('Tamil Nadu', 'Tamil Nadu'), 
                        ('All India', 'All India'), 
                        ('Multiple Cities', 'Multiple Cities'),  
                        ('Maharashtra', 'Maharashtra'), 
                        ('Telangana', 'Telangana'),  
                        ('Andhra Pradesh', 'Andhra Pradesh'),  
                        ('Odisha', 'Odisha'),  
                        ('Gujarat', 'Gujarat'),  
                        ('Chhattisgarh', 'Chhattisgarh'), 
                        ('Madhya Pradesh', 'Madhya Pradesh'),  
                          
                        ('Uttarakhand', 'Uttarakhand'),
                        ('Kerala', 'Kerala'),  
                          
                          ('Ahmedabad', 'Ahmedabad'),
                          ('Rural India', 'Rural India'),  
                    ]

    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=50, choices=SCHEME_CATEGORY_CHOICES, default="None")
    scheme_type = models.CharField(max_length=50, choices=SCHEME_TYPE_CHOICES, default="None")
    description = models.TextField(blank=True, null=True)
    s_eligibility = models.CharField(max_length=100, choices=SCHEME_ELIGIBILITY_CHOICES, blank=True, null=True)  # Increased max_length
    benefits = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, choices=SCHEME_LOCATION_CHOICES, default="None")
    date = models.DateField(blank=True, null=True)  # Single date field to match seed data
    additional_info = models.TextField(blank=True, null=True)
    required_documents = models.TextField(blank=True)
    benefit_amount = models.CharField(max_length=180, blank=True)
    registration_start_date = models.DateField(blank=True, null=True)
    registration_end_date = models.DateField(blank=True, null=True)
    source_name = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(blank=True)
    official_notification_url = models.URLField(blank=True)
    application_url = models.URLField(blank=True)
    is_live_source = models.BooleanField(default=False)
    data_as_of = models.DateField(blank=True, null=True)
    verification_notes = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def effective_deadline(self):
        return self.registration_end_date or self.date

    @property
    def registration_window(self):
        if self.registration_start_date and self.registration_end_date:
            return f"{self.registration_start_date} to {self.registration_end_date}"

        if self.registration_end_date:
            return f"Last date: {self.registration_end_date}"

        if self.registration_start_date:
            return f"Opens: {self.registration_start_date}"

        return "Not listed"

    @property
    def benefit_summary(self):
        return self.benefit_amount or self.benefits or "Not listed"


# -------------------- REAL-WORLD JOB / OPPORTUNITY MODEL --------------------
class JobOpportunity(models.Model):
    OPPORTUNITY_TYPES = [
        ("government_job", "Government Job"),
        ("private_job", "Private Job"),
        ("it_offcampus", "IT Off-Campus"),
        ("internship", "Internship"),
        ("apprenticeship", "Apprenticeship"),
        ("job_fair", "Job Fair"),
        ("career_portal", "Career Portal"),
    ]
    COMPENSATION_TYPES = [
        ("not_listed", "Not Listed"),
        ("ctc", "CTC"),
        ("salary", "Salary"),
        ("stipend", "Stipend"),
        ("pay_scale", "Pay Scale"),
        ("benefit", "Benefit"),
    ]

    title = models.CharField(max_length=255, unique=True)
    company_or_org = models.CharField(max_length=255, blank=True)
    opportunity_type = models.CharField(
        max_length=40,
        choices=OPPORTUNITY_TYPES,
        default="private_job",
    )
    sector = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True, default="All India")
    qualification = models.CharField(max_length=160, blank=True)
    required_skills = models.TextField(blank=True)
    min_10th_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    min_12th_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    salary_or_stipend = models.CharField(max_length=160, blank=True)
    compensation_type = models.CharField(
        max_length=20,
        choices=COMPENSATION_TYPES,
        default="not_listed",
    )
    compensation = models.CharField(max_length=180, blank=True)
    registration_start_date = models.DateField(blank=True, null=True)
    registration_end_date = models.DateField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    source_name = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(blank=True)
    official_notification_url = models.URLField(blank=True)
    application_url = models.URLField(blank=True)
    is_live_source = models.BooleanField(default=True)
    data_as_of = models.DateField(blank=True, null=True)
    verification_notes = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["registration_end_date", "deadline", "title"]

    def __str__(self):
        return self.title

    @property
    def effective_deadline(self):
        return self.registration_end_date or self.deadline

    @property
    def compensation_summary(self):
        return self.compensation or self.salary_or_stipend or "Not listed"

    @property
    def registration_window(self):
        if self.registration_start_date and self.registration_end_date:
            return f"{self.registration_start_date} to {self.registration_end_date}"

        if self.registration_end_date:
            return f"Last date: {self.registration_end_date}"

        if self.registration_start_date:
            return f"Opens: {self.registration_start_date}"

        return "Not listed"


# -------------------- DOCUMENT MODEL --------------------
class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True, null=True)
    file = models.FileField(upload_to='documents/')

    def __str__(self):
        return self.name


# -------------------- USER PROFILE --------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    middle_name = models.CharField(max_length=50, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    college = models.CharField(max_length=100, blank=True)

    EDUCATION_CHOICES = [
        ('High School', 'High School'),
        ('Diploma', 'Diploma'),
        ('Undergraduate', 'Undergraduate'),
        ('Postgraduate', 'Postgraduate'),
        ('PhD', 'PhD'),
    ]
    education = models.CharField(max_length=50, choices=EDUCATION_CHOICES, blank=True)

    INCOME_CHOICES = [
        ('<1 Lakh', '<1 Lakh'),
        ('1-3 Lakhs', '1-3 Lakhs'),
        ('3-5 Lakhs', '3-5 Lakhs'),
        ('5-10 Lakhs', '5-10 Lakhs'),
        ('>10 Lakhs', '>10 Lakhs'),
    ]
    income = models.CharField(max_length=20, choices=INCOME_CHOICES, blank=True)

    location = models.CharField(max_length=100, blank=True)
    nation = models.CharField(max_length=50, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    caste = models.CharField(max_length=50, blank=True)
    interests = models.TextField(blank=True)  # comma-separated
    skills = models.TextField(blank=True)
    class_10_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    class_12_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    graduation_cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    semester_marks = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
