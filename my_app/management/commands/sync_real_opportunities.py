import json
import os
import urllib.error
import urllib.request

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date

from my_app.models import Exam, JobOpportunity, Scheme


AUTHORITATIVE_SOURCE_CARDS = [
    {
        "title": "DRDO INMAS Apprentice Engagement 2026-27",
        "company_or_org": "Institute of Nuclear Medicine and Allied Sciences, DRDO",
        "opportunity_type": "apprenticeship",
        "sector": "Defence Research",
        "location": "Delhi",
        "qualification": "B.Sc., B.Pharma, B.L.I.Sc., Diploma, or ITI in listed disciplines",
        "required_skills": "Science, pharmacy, library science, diploma engineering, ITI trades, merit-based selection",
        "min_10th_percentage": None,
        "min_12th_percentage": None,
        "min_cgpa": None,
        "compensation_type": "stipend",
        "compensation": "Rs. 9,600 to Rs. 12,300 per month, depending on apprentice category",
        "salary_or_stipend": "Rs. 9,600 to Rs. 12,300 per month",
        "registration_start_date": "2026-04-01",
        "registration_end_date": "2026-04-30",
        "deadline": "2026-04-30",
        "data_as_of": "2026-04-25",
        "description": (
            "Official DRDO INMAS engagement for 38 Graduate, Diploma and ITI "
            "apprentices for one year training in FY 2026-27. Candidates must "
            "apply through the NATS/BOAT portal as described in the notification."
        ),
        "source_name": "DRDO",
        "source_url": "https://www.drdo.gov.in/drdo/en/offerings/vacancies/inmas-delhi-invites-application-engagement-apprentics-fy-2026-27",
        "official_notification_url": "https://www.drdo.gov.in/drdo/sites/default/files/vacancy/advtINMAS_APP30032026.pdf",
        "application_url": "https://nats.education.gov.in/",
        "verification_notes": "Official DRDO vacancy page lists advertisement INMAS/IRAC/APPR-01/2026-27 with end date 30-04-2026.",
    },
    {
        "title": "DRDO INMAS Paid Internship 2026",
        "company_or_org": "Institute of Nuclear Medicine and Allied Sciences, DRDO",
        "opportunity_type": "internship",
        "sector": "Defence Research",
        "location": "Delhi",
        "qualification": "Final-year B.E./B.Tech, M.E./M.Tech, M.Sc. or relevant science/engineering students",
        "required_skills": "Computer science, machine learning, biotechnology, biomedical engineering, material science, general sciences",
        "compensation_type": "stipend",
        "compensation": "Rs. 5,000 per month for UG internship; verify PG stipend from official notification",
        "salary_or_stipend": "Rs. 5,000 per month for UG internship",
        "registration_start_date": "2026-03-27",
        "registration_end_date": "2026-04-30",
        "deadline": "2026-04-30",
        "data_as_of": "2026-04-25",
        "description": (
            "Official paid internship opportunity at DRDO INMAS for pursuing "
            "engineering and science UG/PG students for the 2026-27 cycle."
        ),
        "source_name": "DRDO",
        "source_url": "https://www.drdo.gov.in/drdo/en/offerings/vacancies/inmas-delhi-invites-application-paid-internships-pursuing-enggscience-ugpg",
        "official_notification_url": "https://www.drdo.gov.in/drdo/sites/default/files/vacancy/advtINMAS27032026.pdf",
        "application_url": "https://www.drdo.gov.in/drdo/en/offerings/vacancies",
        "verification_notes": "Official DRDO vacancy page lists advertisement INMAS/I.R.A.C./PAIDINTERNSHIP/2026/01 with end date 30-04-2026.",
    },
    {
        "title": "Jammu and Kashmir Bank Apprentice Recruitment 2026",
        "company_or_org": "Jammu and Kashmir Bank",
        "opportunity_type": "apprenticeship",
        "sector": "Banking",
        "location": "Jammu and Kashmir, Ladakh, Delhi, Mumbai, Lucknow, Bengaluru, Mohali",
        "qualification": "Graduate candidates meeting the notification's age and language rules",
        "required_skills": "Banking aptitude, local language, reasoning, quantitative aptitude, English, general awareness",
        "compensation_type": "stipend",
        "compensation": "Rs. 13,500 per month stipend; conveyance support as per official notification",
        "salary_or_stipend": "Rs. 13,500 per month stipend",
        "registration_start_date": "2026-04-20",
        "registration_end_date": "2026-04-26",
        "deadline": "2026-04-26",
        "data_as_of": "2026-04-25",
        "description": (
            "Official J&K Bank apprenticeship recruitment for 614 apprentices "
            "under NATS for a 12-month training period. Apply only after checking "
            "district, language, age, fee and document rules in the notification."
        ),
        "source_name": "J&K Bank",
        "source_url": "https://jkb.bank.in/sites/default/files/2026-04/Apprenticeship%20Notification%202026-27%20new%20%28002%29.pdf",
        "official_notification_url": "https://jkb.bank.in/sites/default/files/2026-04/Apprenticeship%20Notification%202026-27%20new%20%28002%29.pdf",
        "application_url": "https://www.jkb.bank.in/",
        "verification_notes": "Official bank PDF carries Ref. No. JKB/HR/Rectt/2026-182 dated 17-04-2026.",
    },
    {
        "title": "HPCL Graduate Apprentice Trainees 2026-27",
        "company_or_org": "Hindustan Petroleum Corporation Limited",
        "opportunity_type": "apprenticeship",
        "sector": "Oil and Gas",
        "location": "All India",
        "qualification": "Engineering graduates in disciplines listed in the HPCL advertisement",
        "required_skills": "Engineering fundamentals, discipline-specific knowledge, NATS registration",
        "min_10th_percentage": None,
        "min_12th_percentage": None,
        "min_cgpa": None,
        "compensation_type": "stipend",
        "compensation": "Rs. 25,000 per month stipend",
        "salary_or_stipend": "Rs. 25,000 per month stipend",
        "registration_start_date": "2026-02-16",
        "registration_end_date": "2026-03-02",
        "deadline": "2026-03-02",
        "data_as_of": "2026-04-25",
        "description": (
            "Official HPCL Graduate Apprentice Trainee opportunity. The shown "
            "deadline is retained for realistic historical/reference data and may "
            "already be closed; check HPCL Careers for the latest cycle."
        ),
        "source_name": "HPCL Careers",
        "source_url": "https://www.hindustanpetroleum.com/job-openings",
        "official_notification_url": "https://hindustanpetroleum.com/documents/pdf/Engagement_of_HPCL_Graduate_Apprentice_Trainees_2025-26_Advt_English.pdf",
        "application_url": "https://www.hindustanpetroleum.com/job-openings",
        "verification_notes": "HPCL Careers lists Graduate Apprentice Trainees and the advertisement states a fixed monthly stipend.",
    },
    {
        "title": "National Career Service Job Search",
        "company_or_org": "Ministry of Labour & Employment",
        "opportunity_type": "career_portal",
        "sector": "Government and Private Jobs",
        "location": "All India",
        "qualification": "Varies by employer and post",
        "required_skills": "Job search, resume, interview preparation",
        "compensation_type": "not_listed",
        "compensation": "Varies by employer and individual listing",
        "registration_start_date": None,
        "registration_end_date": None,
        "data_as_of": "2026-04-25",
        "description": (
            "Official Indian employment platform for government and private job "
            "search, career counselling, job fairs and training resources."
        ),
        "source_name": "National Career Service",
        "source_url": "https://www.ncs.gov.in/",
        "application_url": "https://www.ncs.gov.in/",
        "verification_notes": "Official NCS portal; individual jobs must be verified inside the portal before applying.",
    },
    {
        "title": "Search Jobs on National Career Service",
        "company_or_org": "National Government Services Portal",
        "opportunity_type": "government_job",
        "sector": "Employment",
        "location": "All India",
        "qualification": "Varies by job listing",
        "required_skills": "Profile matching, location filters, qualification filters",
        "compensation_type": "not_listed",
        "compensation": "Varies by job listing",
        "data_as_of": "2026-04-25",
        "description": (
            "Government Services Portal page that directs job seekers to NCS job "
            "search across sectors, including government and private organizations."
        ),
        "source_name": "services.india.gov.in",
        "source_url": "https://services.india.gov.in/service/detail/national-career-service-job-search",
        "application_url": "https://services.india.gov.in/service/detail/national-career-service-job-search",
        "verification_notes": "Government Services Portal source for NCS job search.",
    },
    {
        "title": "myScheme Government Scheme Finder",
        "company_or_org": "National e-Governance Division",
        "opportunity_type": "career_portal",
        "sector": "Government Schemes",
        "location": "All India",
        "qualification": "Citizen profile based eligibility",
        "required_skills": "Scheme discovery, eligibility check, documents",
        "compensation_type": "benefit",
        "compensation": "Scheme benefits vary by selected scheme",
        "data_as_of": "2026-04-25",
        "description": (
            "Official national platform for discovering central and state government "
            "schemes using demographic, income, social and education attributes."
        ),
        "source_name": "myScheme",
        "source_url": "https://www.myscheme.gov.in/",
        "application_url": "https://www.myscheme.gov.in/find-scheme",
        "verification_notes": "Official myScheme portal; dates and benefits are scheme-specific.",
    },
    {
        "title": "National Scholarship Portal",
        "company_or_org": "Government of India",
        "opportunity_type": "career_portal",
        "sector": "Scholarships",
        "location": "All India",
        "qualification": "Students; varies by scholarship",
        "required_skills": "Academic records, income certificate, category certificate",
        "compensation_type": "benefit",
        "compensation": "Scholarship amount varies by scheme and ministry",
        "data_as_of": "2026-04-25",
        "description": (
            "Central portal for government scholarship applications and student "
            "financial assistance discovery."
        ),
        "source_name": "National Scholarship Portal",
        "source_url": "https://scholarships.gov.in/",
        "application_url": "https://scholarships.gov.in/",
        "verification_notes": "Official scholarship portal; application windows are scheme-specific.",
    },
    {
        "title": "Apprenticeship India Opportunities",
        "company_or_org": "Government of India",
        "opportunity_type": "apprenticeship",
        "sector": "Apprenticeship",
        "location": "All India",
        "qualification": "ITI, Diploma, Graduate and other levels depending on listing",
        "required_skills": "Trade skills, technical skills, workplace learning",
        "compensation_type": "stipend",
        "compensation": "Stipend varies by apprenticeship category and employer listing",
        "data_as_of": "2026-04-25",
        "description": (
            "Official apprenticeship platform for students and freshers looking for "
            "practical industry training opportunities."
        ),
        "source_name": "Apprenticeship India",
        "source_url": "https://www.apprenticeshipindia.gov.in/",
        "application_url": "https://www.apprenticeshipindia.gov.in/",
        "verification_notes": "Official apprenticeship portal; stipend and dates must be checked per establishment.",
    },
    {
        "title": "TCS NextStep / NQT Hiring",
        "company_or_org": "Tata Consultancy Services",
        "opportunity_type": "it_offcampus",
        "sector": "Information Technology",
        "location": "All India",
        "qualification": "Freshers and students; varies by hiring cycle",
        "required_skills": "Programming, aptitude, communication, problem solving",
        "compensation_type": "ctc",
        "compensation": "Not published consistently on official portal; verify current role CTC in the official offer/notification",
        "data_as_of": "2026-04-25",
        "description": (
            "Official TCS careers and fresher hiring portal. Check current cycles "
            "and eligibility from the source before applying."
        ),
        "source_name": "TCS NextStep",
        "source_url": "https://nextstep.tcs.com/",
        "application_url": "https://nextstep.tcs.com/",
        "verification_notes": "Official TCS fresher portal; CTC and registration dates vary by active hiring cycle.",
    },
    {
        "title": "Infosys Careers - Entry Level Jobs",
        "company_or_org": "Infosys",
        "opportunity_type": "it_offcampus",
        "sector": "Information Technology",
        "location": "All India",
        "qualification": "Freshers and graduates; varies by role",
        "required_skills": "Programming, database, aptitude, communication",
        "compensation_type": "ctc",
        "compensation": "Not published consistently on official careers page; verify current CTC in official role details",
        "data_as_of": "2026-04-25",
        "description": (
            "Official Infosys careers source for graduate, fresher and experienced "
            "technology roles."
        ),
        "source_name": "Infosys Careers",
        "source_url": "https://www.infosys.com/careers/",
        "application_url": "https://www.infosys.com/careers/",
        "verification_notes": "Official careers portal; role-specific CTC and deadlines can change by drive.",
    },
    {
        "title": "Wipro Careers - Graduate Hiring",
        "company_or_org": "Wipro",
        "opportunity_type": "it_offcampus",
        "sector": "Information Technology",
        "location": "All India",
        "qualification": "Freshers and graduates; varies by role",
        "required_skills": "Programming, aptitude, English, problem solving",
        "compensation_type": "ctc",
        "compensation": "Not published consistently on official careers page; verify current CTC in official role details",
        "data_as_of": "2026-04-25",
        "description": (
            "Official Wipro careers source for fresher hiring and technology roles."
        ),
        "source_name": "Wipro Careers",
        "source_url": "https://careers.wipro.com/",
        "application_url": "https://careers.wipro.com/",
        "verification_notes": "Official careers portal; role-specific CTC and deadlines can change by drive.",
    },
    {
        "title": "Accenture Careers India",
        "company_or_org": "Accenture",
        "opportunity_type": "it_offcampus",
        "sector": "Information Technology",
        "location": "India",
        "qualification": "Students, graduates and professionals; varies by role",
        "required_skills": "Programming, cloud, data, consulting, communication",
        "compensation_type": "ctc",
        "compensation": "Not published consistently on official careers page; verify current CTC in official role details",
        "data_as_of": "2026-04-25",
        "description": (
            "Official Accenture careers source for India roles and graduate hiring."
        ),
        "source_name": "Accenture Careers",
        "source_url": "https://www.accenture.com/in-en/careers",
        "application_url": "https://www.accenture.com/in-en/careers",
        "verification_notes": "Official careers portal; role-specific CTC and deadlines can change by drive.",
    },
]


INDIAN_EXAM_RECORDS = [
    {
        "name": "UPSC Civil Services Preliminary Examination 2026",
        "exam_type": "Government",
        "category": "Civil Services",
        "location": "All India",
        "mode": "Offline",
        "date": "2026-05-24",
        "e_eligibility": "Graduate",
        "conducting_body": "Union Public Service Commission",
        "registration_start_date": "2026-01-14",
        "registration_end_date": "2026-02-03",
        "application_fee": "Verify from the official UPSC notification; fee is not listed in the annual calendar.",
        "salary_package": "Varies by selected civil service/post; verify pay level in the official notification.",
        "required_skills": "General studies, CSAT aptitude, current affairs, Indian polity, economy, history, geography, environment, essay and analytical writing",
        "additional_info": "Official UPSC calendar lists notification date, application last date and exam commencement date.",
        "source_name": "UPSC Annual Calendar 2026",
        "source_url": "https://upsc.gov.in/examinations/exam-calendar",
        "official_notification_url": "https://upsc.gov.in/sites/default/files/Calendar-2026-Engl-150525_5.pdf",
        "application_url": "https://upsconline.nic.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "Calendar dates are liable to alteration by UPSC.",
    },
    {
        "name": "UPSC Indian Forest Service Preliminary Examination 2026",
        "exam_type": "Government",
        "category": "Civil Services",
        "location": "All India",
        "mode": "Offline",
        "date": "2026-05-24",
        "e_eligibility": "Graduate",
        "conducting_body": "Union Public Service Commission",
        "registration_start_date": "2026-01-14",
        "registration_end_date": "2026-02-03",
        "application_fee": "Verify from the official UPSC notification; fee is not listed in the annual calendar.",
        "salary_package": "Varies by Indian Forest Service rules and pay level; verify official notification.",
        "required_skills": "General studies, CSAT aptitude, forestry/environment awareness, science background as per notification",
        "additional_info": "Preliminary examination is through the Civil Services Preliminary Examination 2026.",
        "source_name": "UPSC Annual Calendar 2026",
        "source_url": "https://upsc.gov.in/examinations/exam-calendar",
        "official_notification_url": "https://upsc.gov.in/sites/default/files/Calendar-2026-Engl-150525_5.pdf",
        "application_url": "https://upsconline.nic.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "Calendar dates are liable to alteration by UPSC.",
    },
    {
        "name": "UPSC IES/ISS Examination 2026",
        "exam_type": "Government",
        "category": "Science",
        "location": "All India",
        "mode": "Offline",
        "date": "2026-06-19",
        "e_eligibility": "Post Graduate",
        "conducting_body": "Union Public Service Commission",
        "registration_start_date": "2026-02-11",
        "registration_end_date": "2026-03-03",
        "application_fee": "Verify from the official UPSC notification; fee is not listed in the annual calendar.",
        "salary_package": "Indian Economic Service / Indian Statistical Service pay varies by service rules; verify official notification.",
        "required_skills": "Economics, statistics, quantitative analysis, data interpretation, general English, general studies",
        "additional_info": "UPSC calendar lists the examination duration as 3 days.",
        "source_name": "UPSC Annual Calendar 2026",
        "source_url": "https://upsc.gov.in/examinations/exam-calendar",
        "official_notification_url": "https://upsc.gov.in/sites/default/files/Calendar-2026-Engl-150525_5.pdf",
        "application_url": "https://upsconline.nic.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "Calendar dates are liable to alteration by UPSC.",
    },
    {
        "name": "UPSC CAPF Assistant Commandants Examination 2026",
        "exam_type": "Government",
        "category": "Defense",
        "location": "All India",
        "mode": "Offline",
        "date": "2026-07-19",
        "e_eligibility": "Graduate",
        "conducting_body": "Union Public Service Commission",
        "registration_start_date": "2026-02-18",
        "registration_end_date": "2026-03-10",
        "application_fee": "Verify from the official UPSC notification; fee is not listed in the annual calendar.",
        "salary_package": "Assistant Commandant pay varies by force and government pay rules; verify official notification.",
        "required_skills": "General ability, intelligence, current affairs, essay writing, physical standards, interview/personality test",
        "additional_info": "UPSC calendar lists the exam commencement date as 19 July 2026.",
        "source_name": "UPSC Annual Calendar 2026",
        "source_url": "https://upsc.gov.in/examinations/exam-calendar",
        "official_notification_url": "https://upsc.gov.in/sites/default/files/Calendar-2026-Engl-150525_5.pdf",
        "application_url": "https://upsconline.nic.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "Calendar dates are liable to alteration by UPSC.",
    },
    {
        "name": "UPSC Combined Medical Services Examination 2026",
        "exam_type": "Government",
        "category": "Medical",
        "location": "All India",
        "mode": "Online",
        "date": "2026-08-02",
        "e_eligibility": "Graduate",
        "conducting_body": "Union Public Service Commission",
        "registration_start_date": "2026-03-11",
        "registration_end_date": "2026-03-31",
        "application_fee": "Verify from the official UPSC notification; fee is not listed in the annual calendar.",
        "salary_package": "Medical officer pay varies by post and department; verify official notification.",
        "required_skills": "MBBS-level medical knowledge, general medicine, paediatrics, surgery, preventive and social medicine",
        "additional_info": "UPSC calendar lists the exam commencement date as 2 August 2026.",
        "source_name": "UPSC Annual Calendar 2026",
        "source_url": "https://upsc.gov.in/examinations/exam-calendar",
        "official_notification_url": "https://upsc.gov.in/sites/default/files/Calendar-2026-Engl-150525_5.pdf",
        "application_url": "https://upsconline.nic.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "Calendar dates are liable to alteration by UPSC.",
    },
    {
        "name": "UPSC NDA and NA Examination II 2026",
        "exam_type": "Government",
        "category": "Defense",
        "location": "All India",
        "mode": "Offline",
        "date": "2026-09-13",
        "e_eligibility": "12th Pass",
        "conducting_body": "Union Public Service Commission",
        "registration_start_date": "2026-05-20",
        "registration_end_date": "2026-06-09",
        "application_fee": "Verify from the official UPSC notification; fee is not listed in the annual calendar.",
        "salary_package": "Training stipend/pay and officer pay rules must be verified from the official NDA notification.",
        "required_skills": "Mathematics, general ability, English, general knowledge, physical fitness, SSB interview readiness",
        "additional_info": "UPSC calendar lists NDA & NA Examination II on 13 September 2026.",
        "source_name": "UPSC Annual Calendar 2026",
        "source_url": "https://upsc.gov.in/examinations/exam-calendar",
        "official_notification_url": "https://upsc.gov.in/sites/default/files/Calendar-2026-Engl-150525_5.pdf",
        "application_url": "https://upsconline.nic.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "Calendar dates are liable to alteration by UPSC.",
    },
    {
        "name": "UPSC CDS Examination II 2026",
        "exam_type": "Government",
        "category": "Defense",
        "location": "All India",
        "mode": "Offline",
        "date": "2026-09-13",
        "e_eligibility": "Graduate",
        "conducting_body": "Union Public Service Commission",
        "registration_start_date": "2026-05-20",
        "registration_end_date": "2026-06-09",
        "application_fee": "Verify from the official UPSC notification; fee is not listed in the annual calendar.",
        "salary_package": "Training stipend/pay and officer pay rules must be verified from the official CDS notification.",
        "required_skills": "English, general knowledge, elementary mathematics where applicable, physical fitness, SSB interview readiness",
        "additional_info": "UPSC calendar lists CDS Examination II on 13 September 2026.",
        "source_name": "UPSC Annual Calendar 2026",
        "source_url": "https://upsc.gov.in/examinations/exam-calendar",
        "official_notification_url": "https://upsc.gov.in/sites/default/files/Calendar-2026-Engl-150525_5.pdf",
        "application_url": "https://upsconline.nic.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "Calendar dates are liable to alteration by UPSC.",
    },
]


INDIAN_SCHEME_RECORDS = [
    {
        "name": "myScheme Government Scheme Finder",
        "category": "General",
        "scheme_type": "Central Government",
        "description": "Official national platform for searching central and state government schemes using citizen attributes.",
        "s_eligibility": "Open to All",
        "benefits": "Scheme benefits vary by selected scheme.",
        "benefit_amount": "Varies by scheme",
        "required_documents": "Varies by scheme; commonly Aadhaar, bank details, income certificate, caste/category certificate, domicile proof and education certificates.",
        "location": "All India",
        "additional_info": "Use this official platform to discover schemes before final application on the linked department portal.",
        "source_name": "myScheme",
        "source_url": "https://www.myscheme.gov.in/",
        "application_url": "https://www.myscheme.gov.in/find-scheme",
        "data_as_of": "2026-04-25",
        "verification_notes": "myScheme is the official NeGD platform for scheme discovery; individual scheme dates and benefits must be checked per scheme page.",
    },
    {
        "name": "National Scholarship Portal",
        "category": "Education",
        "scheme_type": "Scholarship",
        "description": "Official portal for central, state, UGC and AICTE scholarship applications and tracking.",
        "s_eligibility": "Open to All",
        "benefits": "Scholarship amounts vary by ministry, category, course and scheme.",
        "benefit_amount": "Varies by scholarship",
        "required_documents": "Aadhaar/OTR, marksheets, income certificate, caste/category certificate if applicable, bank account details and institute verification.",
        "location": "All India",
        "additional_info": "Students should verify each scholarship window inside the official NSP portal.",
        "source_name": "National Scholarship Portal",
        "source_url": "https://scholarships.gov.in/",
        "application_url": "https://scholarships.gov.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "NSP scholarship deadlines are scheme-specific and may be revised by the respective ministry/department.",
    },
    {
        "name": "PM Internship Scheme",
        "category": "Employment",
        "scheme_type": "Training",
        "description": "Official internship scheme under the Ministry of Corporate Affairs connecting eligible youth with companies for practical work exposure.",
        "s_eligibility": "18+ years",
        "benefits": "Monthly internship assistance and one-time grant as notified on the official PMIS portal.",
        "benefit_amount": "Verify current monthly assistance and one-time grant on the PM Internship portal.",
        "required_documents": "Aadhaar, education certificates, bank details, profile details and declarations requested on the portal.",
        "location": "All India",
        "additional_info": "Registration and internship windows are cycle-based; verify open opportunities on the official portal.",
        "source_name": "PM Internship Scheme",
        "source_url": "https://pminternship.mca.gov.in/",
        "application_url": "https://pminternship.mca.gov.in/",
        "data_as_of": "2026-04-25",
        "verification_notes": "Use the official MCA PM Internship portal for live company opportunities, dates and final benefit details.",
    },
]


class Command(BaseCommand):
    help = (
        "Sync source-backed Indian exams, schemes and job/opportunity cards. "
        "Optional JSON feeds can be supplied through REAL_EXAM_FEEDS, "
        "REAL_SCHEME_FEEDS and REAL_OPPORTUNITY_FEEDS."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace-seed-data",
            action="store_true",
            help=(
                "Delete existing exams, schemes and job opportunities before "
                "syncing source-backed records. Use this when you want the app "
                "not to depend on seed_data.py rows."
            ),
        )

    def handle(self, *args, **options):
        if options.get("replace_seed_data"):
            Exam.objects.all().delete()
            Scheme.objects.all().delete()
            JobOpportunity.objects.all().delete()

        opportunity_count = 0
        exam_count = 0
        scheme_count = 0

        for exam in INDIAN_EXAM_RECORDS:
            self.upsert_exam(exam)
            exam_count += 1

        for scheme in INDIAN_SCHEME_RECORDS:
            self.upsert_scheme(scheme)
            scheme_count += 1

        for source in AUTHORITATIVE_SOURCE_CARDS:
            self.upsert_opportunity(source)
            opportunity_count += 1

        for url in self.feed_urls("REAL_EXAM_FEEDS"):
            exam_count += self.import_json_feed(url, "exam")

        for url in self.feed_urls("REAL_SCHEME_FEEDS"):
            scheme_count += self.import_json_feed(url, "scheme")

        for url in self.feed_urls("REAL_OPPORTUNITY_FEEDS"):
            opportunity_count += self.import_json_feed(url, "job")

        self.stdout.write(
            self.style.SUCCESS(
                "Synced "
                f"{exam_count} exams, "
                f"{scheme_count} schemes, and "
                f"{opportunity_count} real-world opportunity records."
            )
        )

    def feed_urls(self, env_name):
        return [
            url.strip()
            for url in os.environ.get(env_name, "").split(",")
            if url.strip()
        ]

    def import_json_feed(self, url, record_type):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "PGIP/1.0 source sync"},
            )
            with urllib.request.urlopen(request, timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.stdout.write(self.style.WARNING(f"Could not import {url}: {exc}"))
            return 0

        records = payload.get("records", payload if isinstance(payload, list) else [])
        imported = 0

        for record in records:
            if record_type == "exam":
                normalized = self.normalize_exam_record(record, url)
                if normalized:
                    self.upsert_exam(normalized)
                    imported += 1
                continue

            if record_type == "scheme":
                normalized = self.normalize_scheme_record(record, url)
                if normalized:
                    self.upsert_scheme(normalized)
                    imported += 1
                continue

            normalized = self.normalize_feed_record(record, url)
            if normalized:
                self.upsert_opportunity(normalized)
                imported += 1

        return imported

    def normalize_exam_record(self, record, source_url):
        name = record.get("name") or record.get("title") or record.get("exam_name")

        if not name:
            return None

        return {
            "name": str(name)[:255],
            "exam_type": record.get("exam_type") or "Government",
            "category": str(record.get("category") or "Employment")[:50],
            "location": str(record.get("location") or "All India")[:100],
            "mode": record.get("mode") or "Online",
            "date": parse_date(str(record.get("date") or record.get("exam_date") or "")),
            "e_eligibility": str(record.get("e_eligibility") or record.get("eligibility") or "Graduate")[:20],
            "conducting_body": str(record.get("conducting_body") or record.get("organization") or "")[:160],
            "registration_start_date": parse_date(str(record.get("registration_start_date") or record.get("notification_date") or "")),
            "registration_end_date": parse_date(str(record.get("registration_end_date") or record.get("last_date") or "")),
            "application_fee": str(record.get("application_fee") or record.get("fee") or "")[:180],
            "salary_package": str(record.get("salary_package") or record.get("salary") or record.get("pay_scale") or "")[:180],
            "required_skills": record.get("required_skills") or record.get("skills") or "",
            "additional_info": record.get("additional_info") or record.get("description") or "",
            "source_name": str(record.get("source_name") or "External Exam Feed")[:120],
            "source_url": record.get("source_url") or source_url,
            "official_notification_url": record.get("official_notification_url") or "",
            "application_url": record.get("application_url") or record.get("apply_url") or "",
            "data_as_of": parse_date(str(record.get("data_as_of") or "")),
            "verification_notes": record.get("verification_notes") or "",
        }

    def normalize_scheme_record(self, record, source_url):
        name = record.get("name") or record.get("title") or record.get("scheme_name")

        if not name:
            return None

        return {
            "name": str(name)[:255],
            "category": str(record.get("category") or "General")[:50],
            "scheme_type": str(record.get("scheme_type") or "Central Government")[:50],
            "description": record.get("description") or "",
            "s_eligibility": str(record.get("s_eligibility") or record.get("eligibility") or "Open to All")[:100],
            "benefits": record.get("benefits") or "",
            "benefit_amount": str(record.get("benefit_amount") or record.get("amount") or "")[:180],
            "required_documents": record.get("required_documents") or record.get("documents") or "",
            "location": str(record.get("location") or "All India")[:100],
            "date": parse_date(str(record.get("date") or record.get("deadline") or "")),
            "registration_start_date": parse_date(str(record.get("registration_start_date") or record.get("start_date") or "")),
            "registration_end_date": parse_date(str(record.get("registration_end_date") or record.get("last_date") or "")),
            "additional_info": record.get("additional_info") or "",
            "source_name": str(record.get("source_name") or "External Scheme Feed")[:120],
            "source_url": record.get("source_url") or source_url,
            "official_notification_url": record.get("official_notification_url") or "",
            "application_url": record.get("application_url") or record.get("apply_url") or "",
            "data_as_of": parse_date(str(record.get("data_as_of") or "")),
            "verification_notes": record.get("verification_notes") or "",
        }

    def normalize_feed_record(self, record, source_url):
        title = (
            record.get("title")
            or record.get("job_title")
            or record.get("name")
            or record.get("post")
        )

        if not title:
            return None

        return {
            "title": str(title)[:255],
            "company_or_org": str(
                record.get("company")
                or record.get("organization")
                or record.get("department")
                or ""
            )[:255],
            "opportunity_type": record.get("opportunity_type") or "private_job",
            "sector": str(record.get("sector") or record.get("category") or "")[:120],
            "location": str(record.get("location") or "All India")[:120],
            "qualification": str(record.get("qualification") or record.get("eligibility") or "")[:160],
            "required_skills": record.get("skills") or record.get("required_skills") or "",
            "min_10th_percentage": record.get("min_10th_percentage"),
            "min_12th_percentage": record.get("min_12th_percentage"),
            "min_cgpa": record.get("min_cgpa"),
            "salary_or_stipend": str(
                record.get("salary_or_stipend")
                or record.get("salary")
                or record.get("stipend")
                or record.get("ctc")
                or ""
            )[:160],
            "compensation_type": record.get("compensation_type") or self.infer_compensation_type(record),
            "compensation": str(
                record.get("compensation")
                or record.get("salary_or_stipend")
                or record.get("salary")
                or record.get("stipend")
                or record.get("ctc")
                or ""
            )[:180],
            "registration_start_date": parse_date(str(
                record.get("registration_start_date")
                or record.get("apply_start")
                or record.get("start_date")
                or ""
            )),
            "registration_end_date": parse_date(str(
                record.get("registration_end_date")
                or record.get("last_date")
                or record.get("deadline")
                or record.get("end_date")
                or ""
            )),
            "deadline": parse_date(str(record.get("deadline") or record.get("last_date") or "")),
            "description": record.get("description") or "",
            "source_name": str(record.get("source_name") or "External Feed")[:120],
            "source_url": record.get("source_url") or source_url,
            "official_notification_url": record.get("official_notification_url") or "",
            "application_url": record.get("application_url") or record.get("apply_url") or "",
            "data_as_of": parse_date(str(record.get("data_as_of") or "")),
            "verification_notes": record.get("verification_notes") or "",
        }

    def upsert_opportunity(self, data):
        for key in ["deadline", "registration_start_date", "registration_end_date", "data_as_of"]:
            if isinstance(data.get(key), str):
                data[key] = parse_date(data[key])

        if not data.get("deadline"):
            data["deadline"] = data.get("registration_end_date")

        if not data.get("salary_or_stipend"):
            data["salary_or_stipend"] = data.get("compensation", "")[:160]

        data["last_synced_at"] = timezone.now()
        JobOpportunity.objects.update_or_create(
            title=data["title"],
            defaults=data,
        )

    def upsert_exam(self, data):
        for key in ["date", "registration_start_date", "registration_end_date", "data_as_of"]:
            if isinstance(data.get(key), str):
                data[key] = parse_date(data[key])

        data["is_live_source"] = True
        data["last_synced_at"] = timezone.now()
        Exam.objects.update_or_create(
            name=data["name"],
            defaults=data,
        )

    def upsert_scheme(self, data):
        for key in ["date", "registration_start_date", "registration_end_date", "data_as_of"]:
            if isinstance(data.get(key), str):
                data[key] = parse_date(data[key])

        data["is_live_source"] = True
        data["last_synced_at"] = timezone.now()
        Scheme.objects.update_or_create(
            name=data["name"],
            defaults=data,
        )

    def infer_compensation_type(self, record):
        if record.get("ctc"):
            return "ctc"

        if record.get("stipend"):
            return "stipend"

        if record.get("salary"):
            return "salary"

        return "not_listed"
