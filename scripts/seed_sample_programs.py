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
        "institution_slug": "massachusetts-institute-of-technology-mit-united-states",
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
        "institution_slug": "stanford-university-united-states",
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
            {
                "program_name": "Master of Computing in Computer Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": "NUS Computing offers a comprehensive graduate program in computer science.",
                "deadline": date(2026, 3, 15),
                "tuition_usd": Decimal("32000"),
                "duration_months": 18,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "310+", "mandatory": False},
                ],
            },
            {
                "program_name": "Bachelor of Computing in Information Systems",
                "degree_type": DegreeType.BACHELORS,
                "field": "Information Systems",
                "field_category": "Engineering & Technology",
                "description": "An undergraduate program focusing on the intersection of business and technology.",
                "deadline": date(2027, 2, 28),
                "tuition_usd": Decimal("18000"),
                "duration_months": 48,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "requirements": [
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
        ],
    },
    {
        "institution_slug": "eth-zurich-switzerland",
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
        "institution_slug": "harvard-university-united-states",
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
        "institution_slug": "california-institute-of-technology-caltech-united-states",
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
        "institution_slug": "nanyang-technological-university-singapore-ntu-singapore",
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
