from django import forms
from django.contrib.auth.models import User
from .models import Task, UserProfile, Document


# ----------------- Extra Forms -----------------
class EmailForm(forms.Form):
    email = forms.EmailField()


class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class DocumentForm(forms.ModelForm):
    category = forms.ChoiceField(
        choices=[
            ("General", "General Document"),
            ("10th Marksheet", "10th Marksheet"),
            ("12th Marksheet", "12th Marksheet"),
            ("Semester Marksheet", "Semester Marksheet"),
            ("Degree/Certificate", "Degree/Certificate"),
            ("Income Certificate", "Income Certificate"),
            ("Caste Certificate", "Caste Certificate"),
            ("Resume", "Resume"),
        ],
        required=False,
    )

    class Meta:
        model = Document
        fields = ['name', 'category', 'file']


# ----------------- Choice Lists -----------------
RELIGION_CHOICES = [
    ('Hindu', 'Hindu'),
    ('Muslim', 'Muslim'),
    ('Christian', 'Christian'),
    ('Sikh', 'Sikh'),
    ('Buddhist', 'Buddhist'),
    ('Jain', 'Jain'),
    ('Other', 'Other'),
]

CASTE_CHOICES = [
    ('General', 'General'),
    ('OBC', 'OBC'),
    ('SC', 'SC'),
    ('ST', 'ST'),
    ('Other', 'Other'),
]

NATION_CHOICES = [
    ('India', 'India'),
    ('Nepal', 'Nepal'),
    ('Bhutan', 'Bhutan'),
    ('Bangladesh', 'Bangladesh'),
    ('Sri Lanka', 'Sri Lanka'),
    ('Maldives', 'Maldives'),
    ('Pakistan', 'Pakistan'),
    ('Other', 'Other'),
]

INTEREST_CHOICES = [
    ('tech', 'Technology'),
    ('govt', 'Government Schemes'),
    ('exams', 'Competitive Exams'),
    ('health', 'Health & Wellness'),
    ('env', 'Environment'),
    ('startup', 'Startups'),
    ('finance', 'Finance & Taxes'),
    ('jobs', 'Job Updates'),
    ('edu', 'Higher Education'),
    ('scholarships', 'Scholarships'),
    ('welfare', 'Welfare'),
]

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
]


# ----------------- User & Profile Forms -----------------
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class UserProfileForm(forms.ModelForm):
    religion = forms.ChoiceField(choices=RELIGION_CHOICES)
    caste = forms.ChoiceField(choices=CASTE_CHOICES)
    nation = forms.ChoiceField(
        choices=NATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    interests = forms.MultipleChoiceField(
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = [
            'middle_name', 'college', 'dob', 'education', 'income',
            'location', 'nation', 'religion', 'caste', 'interests', 'gender',
            'skills', 'class_10_percentage', 'class_12_percentage',
            'graduation_cgpa', 'semester_marks'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'skills': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Example: Python, SQL, Django, React, Excel'
            }),
            'semester_marks': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Example: Sem 1: 8.1, Sem 2: 8.4, Sem 3: 8.2'
            }),
        }

    def clean_interests(self):
        """Store interests as comma-separated string in DB"""
        return ','.join(self.cleaned_data.get('interests', []))

    def __init__(self, *args, **kwargs):
        """Pre-select interests if already saved as CSV"""
        instance = kwargs.get('instance')
        if instance and instance.interests:
            initial = kwargs.setdefault('initial', {})
            initial['interests'] = instance.interests.split(',')
        super().__init__(*args, **kwargs)
