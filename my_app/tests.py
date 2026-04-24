from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Exam, Scheme, UserProfile
from .services.ai_recommendation import recommend_exams, recommend_schemes


class AiRecommendationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            education="Undergraduate",
            income="<1 Lakh",
            location="All India",
            interests="tech,scholarships",
        )

    def test_recommend_exams_prefers_profile_similarity(self):
        engineering_exam = Exam.objects.create(
            name="Future Engineering Entrance",
            exam_type="National Level",
            category="Engineering",
            location="All India",
            mode="Online",
            date=date(2030, 1, 1),
            e_eligibility="12th Pass",
            additional_info="Computer science engineering technology admission",
        )
        medical_exam = Exam.objects.create(
            name="Regional Medical Test",
            exam_type="State Level",
            category="Medical",
            location="Delhi",
            mode="Offline",
            date=date(2030, 1, 1),
            e_eligibility="Post Graduate",
            additional_info="Healthcare medical admission",
        )

        recommendations = recommend_exams(
            self.profile,
            Exam.objects.all(),
        )

        self.assertEqual(recommendations[0], engineering_exam)
        self.assertIn(medical_exam, recommendations)
        engineering_recommendation = recommendations[0]
        medical_recommendation = next(
            item
            for item in recommendations
            if item == medical_exam
        )

        self.assertGreater(
            engineering_recommendation.ai_score,
            medical_recommendation.ai_score,
        )
        self.assertTrue(engineering_recommendation.ai_reasons)

    def test_recommend_schemes_adds_ai_metadata(self):
        Scheme.objects.create(
            name="Student Scholarship Support",
            category="Education",
            scheme_type="Scholarship",
            description="Scholarship and fee assistance for students",
            s_eligibility="12th Pass",
            benefits="Financial aid for higher education",
            location="All India",
            date=date(2030, 1, 1),
            additional_info="Useful for low income college students",
        )

        recommendations = recommend_schemes(
            self.profile,
            Scheme.objects.all(),
        )

        self.assertEqual(len(recommendations), 1)
        self.assertGreater(recommendations[0].ai_score, 0)
        self.assertTrue(recommendations[0].ai_reasons)
