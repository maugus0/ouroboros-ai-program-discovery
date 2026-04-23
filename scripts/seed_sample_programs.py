#!/usr/bin/env python3
"""
Seed sample programs for top universities.

Usage:
    python scripts/seed_sample_programs.py
"""

import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.models import (
    DegreeType,
    ProgramCreate,
    ProgramMode,
    ProgramRequirementBase,
    RequirementType,
)
from app.repositories import (
    DatabasePoolConfig,
    InstitutionRepository,
    ProgramRepository,
    ProgramRequirementRepository,
    close_pool,
    create_pool,
    run_migrations,
)

setup_logging()
logger = get_logger(__name__)


SAMPLE_PROGRAMS = [
    {
        "institution_slug": "massachusetts-institute-of-technology-mit-united-states-of-america",
        "programs": [
            {
                "program_name": "Master of Science in Computer Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": "The MIT EECS Master's program prepares students for careers in research and industry.",
                "deadline": date(2026, 12, 15),
                "tuition_usd": Decimal("58000"),
                "duration_months": 24,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "Fall",
                "source_url": "https://www.eecs.mit.edu/academics/graduate-programs/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "320+", "mandatory": False},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                    {
                        "type": RequirementType.RECOMMENDATION,
                        "name": "Letters of Recommendation",
                        "value": "3",
                        "mandatory": True,
                    },
                ],
            },
            {
                "program_name": "Bachelor of Science in Electrical Engineering and Computer Science",
                "degree_type": DegreeType.BACHELORS,
                "field": "Electrical Engineering",
                "field_category": "Engineering & Technology",
                "description": "MIT's flagship undergraduate program in electrical engineering and computer science.",
                "deadline": date(2027, 1, 1),
                "tuition_usd": Decimal("60000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "Fall",
                "requirements": [
                    {"type": RequirementType.SAT, "name": "SAT Score", "value": "1500+", "mandatory": False},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                ],
            },
        ],
    },
    {
        "institution_slug": "imperial-college-london-united-kingdom",
        "programs": [
            {
                "program_name": "MSc in Artificial Intelligence and Machine Learning",
                "degree_type": DegreeType.MASTERS,
                "field": "Artificial Intelligence",
                "field_category": "Engineering & Technology",
                "description": "A rigorous program covering the latest advances in AI and machine learning.",
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("45000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "October",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.7", "mandatory": True},
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "7.0", "mandatory": True},
                    {
                        "type": RequirementType.DEGREE,
                        "name": "Bachelor's Degree",
                        "value": "Computer Science or related",
                        "mandatory": True,
                    },
                ],
            },
        ],
    },
    {
        "institution_slug": "stanford-university-united-states-of-america",
        "programs": [
            {
                "program_name": "Master of Science in Data Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Data Science",
                "field_category": "Engineering & Technology",
                "description": "Stanford's interdisciplinary program in data science and analytics.",
                "deadline": date(2026, 12, 1),
                "tuition_usd": Decimal("62000"),
                "duration_months": 18,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "Fall",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "325+", "mandatory": False},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                ],
            },
        ],
    },
    {
        "institution_slug": "national-university-of-singapore-nus-singapore",
        "programs": [
            # ─────────────────────────────────────────────────────────────────────────
            # COMPUTING (Undergraduate)
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Bachelor of Computing in Computer Science",
                "degree_type": DegreeType.BACHELORS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": "NUS flagship computer science program covering algorithms, systems, AI, and software engineering.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.comp.nus.edu.sg/programmes/ug/cs/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Computing in Information Systems",
                "degree_type": DegreeType.BACHELORS,
                "field": "Information Systems",
                "field_category": "Engineering & Technology",
                "description": "Program focusing on the intersection of business and technology, IT solutions and digital transformation.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.comp.nus.edu.sg/programmes/ug/is/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Science in Business Analytics",
                "degree_type": DegreeType.BACHELORS,
                "field": "Business Analytics",
                "field_category": "Business & Management",
                "description": "Joint program between NUS Computing and NUS Business School in data-driven decision making.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.comp.nus.edu.sg/programmes/ug/ba/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Computing in Information Security",
                "degree_type": DegreeType.BACHELORS,
                "field": "Information Security",
                "field_category": "Engineering & Technology",
                "description": "Specialized program in cybersecurity, cryptography, and secure systems development.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.comp.nus.edu.sg/programmes/ug/isec/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # ENGINEERING (Undergraduate)
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Bachelor of Engineering in Mechanical Engineering",
                "degree_type": DegreeType.BACHELORS,
                "field": "Mechanical Engineering",
                "field_category": "Engineering & Technology",
                "description": "Comprehensive mechanical engineering program covering design, manufacturing, and thermal systems.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/me/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Engineering in Electrical Engineering",
                "degree_type": DegreeType.BACHELORS,
                "field": "Electrical Engineering",
                "field_category": "Engineering & Technology",
                "description": "Program in electrical systems, electronics, power systems, and communications.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/ece/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Engineering in Civil Engineering",
                "degree_type": DegreeType.BACHELORS,
                "field": "Civil Engineering",
                "field_category": "Engineering & Technology",
                "description": "Program covering structural engineering, geotechnical, transportation and water resources.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/cee/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Engineering in Chemical Engineering",
                "degree_type": DegreeType.BACHELORS,
                "field": "Chemical Engineering",
                "field_category": "Engineering & Technology",
                "description": "Program in process engineering, materials, biochemical engineering and sustainability.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/chbe/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Engineering in Biomedical Engineering",
                "degree_type": DegreeType.BACHELORS,
                "field": "Biomedical Engineering",
                "field_category": "Engineering & Technology",
                "description": "Interdisciplinary program combining engineering with life sciences and medicine.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/bme/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Engineering in Industrial and Systems Engineering",
                "degree_type": DegreeType.BACHELORS,
                "field": "Industrial Engineering",
                "field_category": "Engineering & Technology",
                "description": "Program focusing on operations research, supply chain, and systems optimization.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/isem/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Engineering in Materials Science",
                "degree_type": DegreeType.BACHELORS,
                "field": "Materials Science",
                "field_category": "Engineering & Technology",
                "description": "Program covering advanced materials, nanotechnology, and materials characterization.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/mse/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # SCIENCE (Undergraduate)
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Bachelor of Science in Data Science and Analytics",
                "degree_type": DegreeType.BACHELORS,
                "field": "Data Science",
                "field_category": "Engineering & Technology",
                "description": "Program combining statistics, computer science, and domain knowledge for data analysis.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.stat.nus.edu.sg/prospective-students/undergraduate/dsa/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Science in Mathematics",
                "degree_type": DegreeType.BACHELORS,
                "field": "Mathematics",
                "field_category": "Natural Sciences",
                "description": "Pure and applied mathematics program with specializations in various mathematical disciplines.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.math.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Science in Physics",
                "degree_type": DegreeType.BACHELORS,
                "field": "Physics",
                "field_category": "Natural Sciences",
                "description": "Comprehensive physics program covering theoretical and experimental physics.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.physics.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Science in Chemistry",
                "degree_type": DegreeType.BACHELORS,
                "field": "Chemistry",
                "field_category": "Natural Sciences",
                "description": "Program in organic, inorganic, physical, and analytical chemistry.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.chemistry.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Science in Life Sciences",
                "degree_type": DegreeType.BACHELORS,
                "field": "Life Sciences",
                "field_category": "Natural Sciences",
                "description": "Program covering molecular biology, genetics, ecology, and biomedical sciences.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.dbs.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Science in Environmental Studies",
                "degree_type": DegreeType.BACHELORS,
                "field": "Environmental Studies",
                "field_category": "Natural Sciences",
                "description": "Interdisciplinary program on environmental science, policy, and sustainability.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.fas.nus.edu.sg/envstudies/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # BUSINESS (Undergraduate)
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Bachelor of Business Administration",
                "degree_type": DegreeType.BACHELORS,
                "field": "Business Administration",
                "field_category": "Business & Management",
                "description": "Flagship business program with specializations in finance, marketing, strategy, and management.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("20000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://bba.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Accountancy",
                "degree_type": DegreeType.BACHELORS,
                "field": "Accountancy",
                "field_category": "Business & Management",
                "description": "Professional accounting program preparing students for CPA certification.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("20000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://biz.nus.edu.sg/programmes/bachelor-of-accountancy/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Science in Real Estate",
                "degree_type": DegreeType.BACHELORS,
                "field": "Real Estate",
                "field_category": "Business & Management",
                "description": "Program covering real estate finance, investment, development, and urban planning.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("20000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://biz.nus.edu.sg/programmes/bsc-real-estate/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # HUMANITIES & SOCIAL SCIENCES (Undergraduate)
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Bachelor of Arts in Economics",
                "degree_type": DegreeType.BACHELORS,
                "field": "Economics",
                "field_category": "Social Sciences",
                "description": "Rigorous economics program covering micro, macro, econometrics and applied economics.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://fass.nus.edu.sg/ecs/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Arts in Psychology",
                "degree_type": DegreeType.BACHELORS,
                "field": "Psychology",
                "field_category": "Social Sciences",
                "description": "Program covering cognitive, clinical, developmental, and social psychology.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://fass.nus.edu.sg/psy/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Arts in Political Science",
                "degree_type": DegreeType.BACHELORS,
                "field": "Political Science",
                "field_category": "Social Sciences",
                "description": "Program covering comparative politics, international relations, and political theory.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://fass.nus.edu.sg/pol/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Arts in Sociology",
                "degree_type": DegreeType.BACHELORS,
                "field": "Sociology",
                "field_category": "Social Sciences",
                "description": "Program studying social structures, institutions, and human behavior in society.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://fass.nus.edu.sg/soc/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Arts in Communications and New Media",
                "degree_type": DegreeType.BACHELORS,
                "field": "Communications",
                "field_category": "Social Sciences",
                "description": "Program covering digital media, journalism, strategic communications, and media studies.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://fass.nus.edu.sg/cnm/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # LAW (Undergraduate)
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Bachelor of Laws (LLB)",
                "degree_type": DegreeType.BACHELORS,
                "field": "Law",
                "field_category": "Law",
                "description": "Premier law program in Asia covering common law, international law, and legal practice.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("22000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://law.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "7.0", "mandatory": True},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # MEDICINE / DENTISTRY / PHARMACY (Undergraduate)
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Bachelor of Medicine and Bachelor of Surgery (MBBS)",
                "degree_type": DegreeType.BACHELORS,
                "field": "Medicine",
                "field_category": "Health Sciences",
                "description": "Medical degree program training future physicians with clinical rotations at NUH.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("35000"),
                "duration_months": 60,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://medicine.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "7.0", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Dental Surgery (BDS)",
                "degree_type": DegreeType.BACHELORS,
                "field": "Dentistry",
                "field_category": "Health Sciences",
                "description": "Professional dentistry program covering oral health, surgery, and dental sciences.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("35000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://dentistry.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "7.0", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Pharmacy",
                "degree_type": DegreeType.BACHELORS,
                "field": "Pharmacy",
                "field_category": "Health Sciences",
                "description": "Professional pharmacy program covering pharmaceutical sciences and clinical practice.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("25000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://pharmacy.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # ARCHITECTURE & DESIGN (Undergraduate)
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Bachelor of Architecture",
                "degree_type": DegreeType.BACHELORS,
                "field": "Architecture",
                "field_category": "Arts & Design",
                "description": "Professional architecture program covering design, urban planning, and sustainable buildings.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("20000"),
                "duration_months": 60,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/arch/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Bachelor of Arts in Industrial Design",
                "degree_type": DegreeType.BACHELORS,
                "field": "Industrial Design",
                "field_category": "Arts & Design",
                "description": "Program in product design, user experience, and design thinking methodologies.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("20000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://cde.nus.edu.sg/did/",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # POSTGRADUATE - MASTER'S DEGREES
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "Master of Computing in Computer Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": "NUS Computing offers a comprehensive graduate program in computer science with research and coursework tracks.",
                "deadline": date(2026, 3, 15),
                "tuition_usd": Decimal("32000"),
                "duration_months": 18,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.comp.nus.edu.sg/programmes/pg/mcs/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "310+", "mandatory": False},
                ],
            },
            {
                "program_name": "Master of Science in Business Analytics",
                "degree_type": DegreeType.MASTERS,
                "field": "Business Analytics",
                "field_category": "Business & Management",
                "description": "Program combining data science with business strategy for analytics leadership roles.",
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("45000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://msba.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.GMAT, "name": "GMAT", "value": "650+", "mandatory": False},
                ],
            },
            {
                "program_name": "Master of Business Administration (MBA)",
                "degree_type": DegreeType.MASTERS,
                "field": "Business Administration",
                "field_category": "Business & Management",
                "description": "NUS MBA ranked among top programs in Asia, with strong focus on leadership and strategy.",
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("65000"),
                "duration_months": 17,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://mba.nus.edu.sg/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                    {"type": RequirementType.GMAT, "name": "GMAT", "value": "680+", "mandatory": True},
                    {"type": RequirementType.WORK_EXPERIENCE, "name": "Work Experience", "value": "2+ years", "mandatory": True},
                ],
            },
            {
                "program_name": "Master of Science in Finance",
                "degree_type": DegreeType.MASTERS,
                "field": "Finance",
                "field_category": "Business & Management",
                "description": "Rigorous finance program covering quantitative finance, investments, and corporate finance.",
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("50000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://biz.nus.edu.sg/graduate/msf/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                    {"type": RequirementType.GMAT, "name": "GMAT", "value": "700+", "mandatory": False},
                ],
            },
            {
                "program_name": "Master of Science in Data Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Data Science",
                "field_category": "Engineering & Technology",
                "description": "Comprehensive data science program covering machine learning, statistics, and big data.",
                "deadline": date(2026, 3, 15),
                "tuition_usd": Decimal("35000"),
                "duration_months": 18,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.stat.nus.edu.sg/prospective-students/graduate/msc-data-science-analytics/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                ],
            },
            {
                "program_name": "Master of Science in Economics",
                "degree_type": DegreeType.MASTERS,
                "field": "Economics",
                "field_category": "Social Sciences",
                "description": "Advanced economics program with focus on applied and quantitative economics.",
                "deadline": date(2026, 3, 15),
                "tuition_usd": Decimal("30000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://fass.nus.edu.sg/ecs/graduate-programmes/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "Preferred", "mandatory": False},
                ],
            },
            # ─────────────────────────────────────────────────────────────────────────
            # POSTGRADUATE - PHD PROGRAMS
            # ─────────────────────────────────────────────────────────────────────────
            {
                "program_name": "PhD in Computer Science",
                "degree_type": DegreeType.PHD,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": "Research doctorate in computer science with full funding available for qualified candidates.",
                "deadline": date(2026, 1, 15),
                "tuition_usd": Decimal("0"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August/January",
                "source_url": "https://www.comp.nus.edu.sg/programmes/pg/phd/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "Recommended", "mandatory": False},
                    {"type": RequirementType.RECOMMENDATION, "name": "Letters of Recommendation", "value": "3", "mandatory": True},
                ],
            },
            {
                "program_name": "PhD in Engineering",
                "degree_type": DegreeType.PHD,
                "field": "Engineering",
                "field_category": "Engineering & Technology",
                "description": "Research doctorate across engineering disciplines with full scholarship support.",
                "deadline": date(2026, 1, 15),
                "tuition_usd": Decimal("0"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August/January",
                "source_url": "https://cde.nus.edu.sg/graduate/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.RECOMMENDATION, "name": "Letters of Recommendation", "value": "3", "mandatory": True},
                ],
            },
            {
                "program_name": "PhD in Business",
                "degree_type": DegreeType.PHD,
                "field": "Business",
                "field_category": "Business & Management",
                "description": "Research doctorate preparing students for academic careers in business disciplines.",
                "deadline": date(2026, 1, 15),
                "tuition_usd": Decimal("0"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://biz.nus.edu.sg/graduate/phd/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                    {"type": RequirementType.GMAT, "name": "GMAT/GRE", "value": "Required", "mandatory": True},
                    {"type": RequirementType.RECOMMENDATION, "name": "Letters of Recommendation", "value": "3", "mandatory": True},
                ],
            },
            {
                "program_name": "PhD in Social Sciences",
                "degree_type": DegreeType.PHD,
                "field": "Social Sciences",
                "field_category": "Social Sciences",
                "description": "Research doctorate in sociology, political science, economics, or geography.",
                "deadline": date(2026, 1, 15),
                "tuition_usd": Decimal("0"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://fass.nus.edu.sg/graduate-programmes/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                    {"type": RequirementType.RECOMMENDATION, "name": "Letters of Recommendation", "value": "3", "mandatory": True},
                ],
            },
        ],
    },
    {
        "institution_slug": "eth-zurich-swiss-federal-institute-of-technology-switzerland",
        "programs": [
            {
                "program_name": "Master in Robotics, Systems and Control",
                "degree_type": DegreeType.MASTERS,
                "field": "Robotics",
                "field_category": "Engineering & Technology",
                "description": "ETH Zurich's world-renowned program in robotics and autonomous systems.",
                "deadline": date(2026, 12, 15),
                "tuition_usd": Decimal("1500"),
                "duration_months": 24,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "September",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {
                        "type": RequirementType.DEGREE,
                        "name": "Bachelor's Degree",
                        "value": "Engineering or related",
                        "mandatory": True,
                    },
                ],
            },
        ],
    },
    {
        "institution_slug": "university-of-oxford-united-kingdom",
        "programs": [
            {
                "program_name": "MSc in Computer Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": "Oxford's intensive one-year master's program in computer science.",
                "deadline": date(2026, 3, 1),
                "tuition_usd": Decimal("42000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "October",
                "requirements": [
                    {
                        "type": RequirementType.GPA,
                        "name": "First-class Honours",
                        "value": "First or Upper Second",
                        "mandatory": True,
                    },
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "7.5", "mandatory": True},
                    {
                        "type": RequirementType.RECOMMENDATION,
                        "name": "Academic References",
                        "value": "3",
                        "mandatory": True,
                    },
                ],
            },
        ],
    },
    {
        "institution_slug": "university-of-cambridge-united-kingdom",
        "programs": [
            {
                "program_name": "MPhil in Advanced Computer Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": "Cambridge's advanced master's program focusing on cutting-edge computer science research.",
                "deadline": date(2026, 1, 5),
                "tuition_usd": Decimal("45000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "October",
                "requirements": [
                    {
                        "type": RequirementType.GPA,
                        "name": "First-class Honours",
                        "value": "First or equivalent",
                        "mandatory": True,
                    },
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "7.5", "mandatory": True},
                ],
            },
        ],
    },
    {
        "institution_slug": "harvard-university-united-states-of-america",
        "programs": [
            {
                "program_name": "Master of Science in Data Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Data Science",
                "field_category": "Engineering & Technology",
                "description": "Harvard's interdisciplinary data science program combining statistics and computer science.",
                "deadline": date(2026, 12, 15),
                "tuition_usd": Decimal("65000"),
                "duration_months": 16,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "Fall",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "Recommended", "mandatory": False},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                ],
            },
        ],
    },
    {
        "institution_slug": "california-institute-of-technology-caltech-united-states-of-america",
        "programs": [
            {
                "program_name": "PhD in Computer Science",
                "degree_type": DegreeType.PHD,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": "Caltech's doctoral program in computer science with full funding.",
                "deadline": date(2026, 12, 15),
                "tuition_usd": Decimal("0"),
                "duration_months": 60,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "Fall",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.5", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "Not required", "mandatory": False},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "100", "mandatory": True},
                    {
                        "type": RequirementType.RECOMMENDATION,
                        "name": "Letters of Recommendation",
                        "value": "3",
                        "mandatory": True,
                    },
                ],
            },
        ],
    },
    {
        "institution_slug": "nanyang-technological-university-singapore-ntu-singapore-singapore",
        "programs": [
            {
                "program_name": "Master of Science in Artificial Intelligence",
                "degree_type": DegreeType.MASTERS,
                "field": "Artificial Intelligence",
                "field_category": "Engineering & Technology",
                "description": "NTU's comprehensive AI program covering machine learning, deep learning, and applications.",
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("28000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {
                        "type": RequirementType.WORK_EXPERIENCE,
                        "name": "Work Experience",
                        "value": "Preferred",
                        "mandatory": False,
                    },
                ],
            },
        ],
    },
]


async def seed_sample_programs():
    """Seed sample programs into the database."""
    pool = await create_pool(
        DatabasePoolConfig(
            host=settings.get_db_host(),
            port=settings.get_db_port(),
            db=settings.get_db_name(),
            user=settings.get_db_user(),
            password=settings.get_db_password(),
        )
    )

    await run_migrations(pool)

    institution_repo = InstitutionRepository()
    program_repo = ProgramRepository()
    requirement_repo = ProgramRequirementRepository()

    programs_created = 0
    requirements_created = 0

    for item in SAMPLE_PROGRAMS:
        slug = item["institution_slug"]

        institution = await institution_repo.get_by_slug(slug)
        if not institution:
            logger.warning("institution_not_found", slug=slug)
            continue

        for prog_data in item["programs"]:
            try:
                program = await program_repo.create(
                    ProgramCreate(
                        institution_id=institution.id,
                        program_name=prog_data["program_name"],
                        degree_type=prog_data["degree_type"],
                        field=prog_data["field"],
                        field_category=prog_data.get("field_category"),
                        description=prog_data.get("description"),
                        deadline=prog_data.get("deadline"),
                        tuition_usd=prog_data.get("tuition_usd"),
                        duration_months=prog_data.get("duration_months"),
                        language=prog_data.get("language", "English"),
                        mode=prog_data.get("mode", ProgramMode.ON_CAMPUS),
                        intake=prog_data.get("intake"),
                        source_url=prog_data.get("source_url"),
                    )
                )
                programs_created += 1

                if "requirements" in prog_data:
                    requirements = [
                        ProgramRequirementBase(
                            requirement_type=req["type"],
                            requirement_name=req["name"],
                            requirement_value=req.get("value"),
                            is_mandatory=req.get("mandatory", True),
                        )
                        for req in prog_data["requirements"]
                    ]
                    await requirement_repo.create_batch(program.id, requirements)
                    requirements_created += len(requirements)

                logger.info(
                    "program_created",
                    name=prog_data["program_name"],
                    institution=institution.name,
                )

            except Exception as exc:
                logger.error(
                    "program_create_failed",
                    error=str(exc),
                    name=prog_data.get("program_name"),
                )

    await close_pool()

    logger.info(
        "seed_completed",
        programs=programs_created,
        requirements=requirements_created,
    )


if __name__ == "__main__":
    asyncio.run(seed_sample_programs())
