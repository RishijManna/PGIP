from datetime import date

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from .models import Exam, JobOpportunity, Scheme, Task, UserProfile
from .services.ai_assistant import answer_question
from .services.ai_recommendation import (
    build_eligibility_explanation,
    recommend_exams,
    recommend_jobs,
    recommend_schemes,
)


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
            skills="Python, SQL, Django",
            class_10_percentage=88,
            class_12_percentage=84,
            graduation_cgpa=8.2,
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

    def test_eligibility_explanation_includes_verdict_and_documents(self):
        scheme = Scheme.objects.create(
            name="Low Income Student Grant",
            category="Education",
            scheme_type="Scholarship",
            description="Financial assistance for low income students",
            s_eligibility="12th Pass",
            benefits="Fee support and bank transfer",
            location="All India",
            date=date(2030, 1, 1),
            additional_info="Income certificate required",
        )

        explanation = build_eligibility_explanation(
            self.profile,
            scheme,
            "scheme",
        )

        self.assertIn(explanation["verdict"], ["Strong match", "Possible match"])
        self.assertGreaterEqual(explanation["confidence"], 50)
        self.assertTrue(explanation["matching_factors"])
        self.assertIn("Income certificate", explanation["suggested_documents"])

    def test_ai_assistant_returns_grounded_local_answer(self):
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

        result = answer_question(
            self.profile,
            "Which scholarships am I eligible for?",
            Exam.objects.none(),
            Scheme.objects.all(),
        )

        self.assertIn("answer", result)
        self.assertEqual(result["provider"], "local-semantic-rag")
        self.assertTrue(result["items"])
        self.assertIn("Student Scholarship Support", result["items"][0]["title"])

    def test_ai_assistant_page_and_api_render_for_logged_in_user(self):
        Scheme.objects.create(
            name="All India Education Aid",
            category="Education",
            scheme_type="Scholarship",
            description="Support for students",
            s_eligibility="12th Pass",
            benefits="Financial aid",
            location="All India",
            date=date(2030, 1, 1),
        )

        self.client.force_login(self.user)

        page_response = self.client.get("/ai-assistant/")
        self.assertEqual(page_response.status_code, 200)
        self.assertContains(page_response, "PGIP AI Chat")

        api_response = self.client.post(
            "/api/ai-assistant/",
            data='{"message": "Which education schemes match me?"}',
            content_type="application/json",
        )

        self.assertEqual(api_response.status_code, 200)
        self.assertIn("answer", api_response.json())

    def test_job_recommendation_uses_skills_and_marks(self):
        job = JobOpportunity.objects.create(
            title="Django Developer Fresher",
            company_or_org="Example Tech",
            opportunity_type="it_offcampus",
            sector="Information Technology",
            location="All India",
            qualification="Graduate",
            required_skills="Python, Django, SQL",
            min_10th_percentage=60,
            min_12th_percentage=60,
            min_cgpa=6.5,
            source_name="Example Careers",
            source_url="https://example.com/careers",
        )

        recommendations = recommend_jobs(
            self.profile,
            JobOpportunity.objects.all(),
        )

        self.assertEqual(recommendations[0], job)
        self.assertGreater(recommendations[0].ai_score, 0)
        self.assertTrue(
            any("skill match" in reason for reason in recommendations[0].ai_reasons)
        )

    def test_job_recommendation_falls_back_to_live_source_jobs(self):
        blank_user = User.objects.create_user(
            username="blank-profile@example.com",
            email="blank-profile@example.com",
        )
        blank_profile = UserProfile.objects.create(user=blank_user)
        job = JobOpportunity.objects.create(
            title="General Careers Portal",
            company_or_org="Example Source",
            opportunity_type="career_portal",
            sector="Employment",
            location="Unknown Region",
            qualification="Varies",
            source_name="Example Source",
            source_url="https://example.com/jobs",
            is_live_source=True,
        )

        recommendations = recommend_jobs(
            blank_profile,
            JobOpportunity.objects.all(),
        )

        self.assertIn(job, recommendations)
        self.assertGreater(recommendations[0].ai_score, 0)
        self.assertTrue(
            any(
                reason in recommendations[0].ai_reasons
                for reason in ["verified source", "active opportunity channel"]
            )
        )

    def test_calendar_api_includes_dated_job_opportunities(self):
        job = JobOpportunity.objects.create(
            title="DRDO Apprentice Example",
            company_or_org="DRDO",
            opportunity_type="apprenticeship",
            sector="Defence Research",
            location="Delhi",
            qualification="Graduate",
            registration_end_date=date(2030, 4, 30),
            compensation_type="stipend",
            compensation="Rs. 12,300 per month",
            source_name="DRDO",
            source_url="https://example.com/drdo",
        )

        self.client.force_login(self.user)
        response = self.client.get("/api/events/")

        self.assertEqual(response.status_code, 200)
        job_events = [
            event
            for event in response.json()
            if event["id"] == f"job-{job.id}"
        ]
        self.assertEqual(len(job_events), 1)
        self.assertEqual(job_events[0]["start"], "2030-04-30")
        self.assertEqual(job_events[0]["compensation"], "Rs. 12,300 per month")

    def test_add_to_calendar_uses_job_effective_deadline(self):
        job = JobOpportunity.objects.create(
            title="Bank Apprentice Example",
            company_or_org="Example Bank",
            opportunity_type="apprenticeship",
            sector="Banking",
            location="All India",
            qualification="Graduate",
            registration_end_date=date(2030, 5, 15),
            source_name="Example Bank",
            source_url="https://example.com/bank",
        )

        self.client.force_login(self.user)
        response = self.client.post(
            "/add-to-calendar/",
            {"item_type": "job", "item_id": job.id},
            HTTP_REFERER="/",
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Task.objects.filter(
                user=self.user,
                title=f"Job: {job.title}",
                date=date(2030, 5, 15),
            ).exists()
        )

    def test_real_source_sync_can_replace_seed_data(self):
        Exam.objects.create(
            name="Seed Exam To Replace",
            exam_type="Government",
            category="Engineering",
            location="All India",
            mode="Online",
            e_eligibility="Graduate",
        )
        Scheme.objects.create(
            name="Seed Scheme To Replace",
            category="Education",
            scheme_type="Scholarship",
            location="All India",
            s_eligibility="Open to All",
        )

        call_command("sync_real_opportunities", "--replace-seed-data", verbosity=0)

        self.assertFalse(Exam.objects.filter(name="Seed Exam To Replace").exists())
        self.assertFalse(Scheme.objects.filter(name="Seed Scheme To Replace").exists())
        self.assertGreaterEqual(Exam.objects.filter(is_live_source=True).count(), 7)
        self.assertGreaterEqual(Scheme.objects.filter(is_live_source=True).count(), 3)
        self.assertGreaterEqual(JobOpportunity.objects.filter(is_live_source=True).count(), 13)

    def test_recommendations_view_bootstraps_source_backed_records(self):
        self.client.force_login(self.user)

        response = self.client.get("/recommendations/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommended Jobs")
        self.assertGreater(JobOpportunity.objects.count(), 0)
