#!/usr/bin/env python3
"""
Seed Computer Science and related programs from Singapore universities.

Includes programs from:
- Nanyang Technological University (NTU)
- Singapore Management University (SMU)
- Singapore University of Technology and Design (SUTD)

Usage:
    python scripts/seed_singapore_cs_programs.py
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
    ProgramRequirementCreate,
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


SINGAPORE_CS_PROGRAMS = [
    # ─────────────────────────────────────────────────────────────────────────────
    # NANYANG TECHNOLOGICAL UNIVERSITY (NTU) - Computer Science & Related
    # Slug generated from: "Nanyang Technological University, Singapore (NTU Singapore)" + "Singapore"
    # ─────────────────────────────────────────────────────────────────────────────
    {
        "institution_slug": "nanyang-technological-university-singapore-ntu-singapore-singapore",
        "programs": [
            {
                "program_name": "Master of Science in Data Science",
                "degree_type": DegreeType.MASTERS,
                "field": "Data Science",
                "field_category": "Engineering & Technology",
                "description": (
                    "NTU's MSDS programme provides robust training in Data Science with an "
                    "interdisciplinary approach. Courses cover data collection, management, "
                    "analysis, visualization and machine learning. Led by the College of "
                    "Computing and Data Science (CCDS) with faculty from multiple schools."
                ),
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("45000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.ntu.edu.sg/computing/admissions/graduate-programmes/detail/master-of-science-in-data-science-(msds)",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                    {"type": RequirementType.OTHER, "name": "Background", "value": "Computer Science or related discipline", "mandatory": True},
                ],
            },
            {
                "program_name": "Master of Science in Artificial Intelligence",
                "degree_type": DegreeType.MASTERS,
                "field": "Artificial Intelligence",
                "field_category": "Engineering & Technology",
                "description": (
                    "NTU's MSAI programme provides comprehensive training in AI fundamentals "
                    "and applications. Covers machine learning, deep learning, computer vision, "
                    "NLP, and responsible AI development. Strong industry connections."
                ),
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("48000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.ntu.edu.sg/computing/admissions/graduate-programmes",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.2", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE General", "value": "310+", "mandatory": False},
                    {"type": RequirementType.OTHER, "name": "Background", "value": "Computer Science, Mathematics, or Engineering", "mandatory": True},
                ],
            },
            {
                "program_name": "Master of Computing in Applied AI",
                "degree_type": DegreeType.MASTERS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": (
                    "NTU's MCAAI programme equips professionals with skills to apply responsible "
                    "AI in solving real-world problems across industries. Focuses on practical "
                    "AI implementation with ethical considerations."
                ),
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("46000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.ntu.edu.sg/computing/admissions/graduate-programmes",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.WORK_EXPERIENCE, "name": "Work Experience", "value": "2+ years preferred", "mandatory": False},
                ],
            },
            {
                "program_name": "Master of Science in Cyber Security",
                "degree_type": DegreeType.MASTERS,
                "field": "Cybersecurity",
                "field_category": "Engineering & Technology",
                "description": (
                    "NTU's MSCS programme provides advanced training in cybersecurity, covering "
                    "network security, cryptography, digital forensics, and security management. "
                    "Prepares students for leadership roles in cybersecurity."
                ),
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("44000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.ntu.edu.sg/computing/admissions/graduate-programmes",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.OTHER, "name": "Background", "value": "Computer Science, IT, or related discipline", "mandatory": True},
                ],
            },
            {
                "program_name": "Master of Science in Blockchain",
                "degree_type": DegreeType.MASTERS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": (
                    "NTU's blockchain programme covers distributed ledger technology, smart contracts, "
                    "cryptocurrency systems, and decentralized applications. Combines technical depth "
                    "with business applications of blockchain."
                ),
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("42000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://www.ntu.edu.sg/computing/admissions/graduate-programmes",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                ],
            },
        ],
    },
    # ─────────────────────────────────────────────────────────────────────────────
    # SINGAPORE MANAGEMENT UNIVERSITY (SMU)
    # Slug generated from: "Singapore Management University" + "Singapore"
    # ─────────────────────────────────────────────────────────────────────────────
    {
        "institution_slug": "singapore-management-university-singapore",
        "programs": [
            {
                "program_name": "Master of Science in Computing",
                "degree_type": DegreeType.MASTERS,
                "field": "Computer Science",
                "field_category": "Engineering & Technology",
                "description": (
                    "SMU's MSc Computing programme enhances knowledge and skills with a broad view "
                    "of information systems and hands-on experience. Offers tracks in Data Science & "
                    "Engineering, Cybersecurity, and Software & Cyber-Physical Systems."
                ),
                "deadline": date(2026, 4, 30),
                "tuition_usd": Decimal("32000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://computing.smu.edu.sg/mscomputing",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                    {"type": RequirementType.GRE, "name": "GRE/GMAT", "value": "Required", "mandatory": True},
                ],
            },
            {
                "program_name": "Master of IT in Business (Analytics Track)",
                "degree_type": DegreeType.MASTERS,
                "field": "Data Science",
                "field_category": "Engineering & Technology",
                "description": (
                    "SMU's MITB Analytics track equips students with skills in data analytics, "
                    "machine learning, and business intelligence. Designed for professionals "
                    "seeking to leverage data for business decisions."
                ),
                "deadline": date(2026, 4, 30),
                "tuition_usd": Decimal("35000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "August",
                "source_url": "https://computing.smu.edu.sg/programmes/master-it-business",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.WORK_EXPERIENCE, "name": "Work Experience", "value": "2+ years recommended", "mandatory": False},
                ],
            },
        ],
    },
    # ─────────────────────────────────────────────────────────────────────────────
    # SINGAPORE UNIVERSITY OF TECHNOLOGY AND DESIGN (SUTD)
    # Slug generated from: "Singapore University of Technology and Design" + "Singapore"
    # ─────────────────────────────────────────────────────────────────────────────
    {
        "institution_slug": "singapore-university-of-technology-and-design-singapore",
        "programs": [
            {
                "program_name": "Master of Science in Technology and Design (Artificial Intelligence)",
                "degree_type": DegreeType.MASTERS,
                "field": "Artificial Intelligence",
                "field_category": "Engineering & Technology",
                "description": (
                    "SUTD's AI programme blends artificial intelligence with design thinking for "
                    "real-world impact. Covers deep learning, computer vision, NLP, and AI system "
                    "design with emphasis on ethical and responsible AI development."
                ),
                "deadline": date(2026, 5, 31),
                "tuition_usd": Decimal("38000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "September",
                "source_url": "https://www.sutd.edu.sg/admissions/graduate/masters/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.IELTS, "name": "IELTS", "value": "6.5", "mandatory": True},
                ],
            },
            {
                "program_name": "Master of Science in Technology and Design (Cybersecurity)",
                "degree_type": DegreeType.MASTERS,
                "field": "Cybersecurity",
                "field_category": "Engineering & Technology",
                "description": (
                    "SUTD's Cybersecurity programme develops design innovation expertise with IT security. "
                    "Covers network security, cryptography, threat analysis, and security architecture "
                    "with hands-on projects and industry collaboration."
                ),
                "deadline": date(2026, 5, 31),
                "tuition_usd": Decimal("36000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "September",
                "source_url": "https://www.sutd.edu.sg/admissions/graduate/masters/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                ],
            },
            {
                "program_name": "Master of Science in Design and Artificial Intelligence for Enterprise",
                "degree_type": DegreeType.MASTERS,
                "field": "Artificial Intelligence",
                "field_category": "Engineering & Technology",
                "description": (
                    "SUTD's DAIE programme trains students to design, build and deploy enterprise "
                    "AI systems through a structured 9-course curriculum and a year-long industry "
                    "studio experience. Strong focus on practical AI implementation."
                ),
                "deadline": date(2026, 3, 31),
                "tuition_usd": Decimal("40000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "September",
                "source_url": "https://www.sutd.edu.sg/admissions/graduate/masters/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                    {"type": RequirementType.WORK_EXPERIENCE, "name": "Work Experience", "value": "Preferred", "mandatory": False},
                ],
            },
            {
                "program_name": "Master of Science in Security by Design",
                "degree_type": DegreeType.MASTERS,
                "field": "Cybersecurity",
                "field_category": "Engineering & Technology",
                "description": (
                    "SUTD's Security by Design programme integrates security principles into "
                    "system design from the ground up. Covers secure software development, "
                    "threat modeling, and security architecture for modern systems."
                ),
                "deadline": date(2026, 5, 31),
                "tuition_usd": Decimal("35000"),
                "duration_months": 12,
                "language": "English",
                "mode": ProgramMode.ON_CAMPUS,
                "intake": "September",
                "source_url": "https://www.sutd.edu.sg/admissions/graduate/masters/",
                "requirements": [
                    {"type": RequirementType.GPA, "name": "Minimum GPA", "value": "3.0", "mandatory": True},
                    {"type": RequirementType.TOEFL, "name": "TOEFL iBT", "value": "90", "mandatory": True},
                ],
            },
        ],
    },
]


async def seed_programs():
    """Seed Singapore CS programs."""
    logger.info("seed_singapore_cs_programs_starting")

    pool_config = DatabasePoolConfig(
        host=settings.get_db_host(),
        port=settings.get_db_port(),
        db=settings.get_db_name(),
        user=settings.get_db_user(),
        password=settings.get_db_password(),
    )
    await create_pool(pool_config)

    try:
        await run_migrations()
    except Exception as exc:
        logger.warning("migrations_skipped", error=str(exc))

    institution_repo = InstitutionRepository()
    program_repo = ProgramRepository()
    requirement_repo = ProgramRequirementRepository()

    total_programs = 0
    total_requirements = 0

    for entry in SINGAPORE_CS_PROGRAMS:
        slug = entry["institution_slug"]
        institution = await institution_repo.get_by_slug(slug)

        if not institution:
            logger.warning("institution_not_found", slug=slug)
            print(f"  ! Institution not found: {slug}")
            continue

        print(f"\n=== {institution.name} ===")
        logger.info("seeding_institution_programs", institution=institution.name, slug=slug)

        for prog_data in entry["programs"]:
            requirements_data = prog_data.pop("requirements", [])

            program_create = ProgramCreate(
                institution_id=str(institution.id),
                **prog_data,
            )

            try:
                program = await program_repo.create(program_create)
                program_id = str(program.id)
                total_programs += 1
                print(f"  + Created: {prog_data['program_name']} ({program_id})")
                logger.info("program_created", program=prog_data["program_name"], id=program_id)

                for req in requirements_data:
                    try:
                        req_create = ProgramRequirementCreate(
                            program_id=program_id,
                            requirement_type=req["type"],
                            requirement_name=req["name"],
                            requirement_value=req["value"],
                            is_mandatory=req.get("mandatory", True),
                        )
                        await requirement_repo.create(req_create)
                        total_requirements += 1
                    except Exception as exc:
                        logger.warning("requirement_create_failed", error=str(exc), req=req["name"])
            except Exception as exc:
                if "Duplicate" in str(exc) or "duplicate" in str(exc):
                    print(f"  ~ Exists: {prog_data['program_name']}")
                    logger.info("program_exists", program=prog_data["program_name"])
                else:
                    print(f"  ! Error: {prog_data['program_name']}: {exc}")
                    logger.warning("program_create_failed", error=str(exc), program=prog_data["program_name"])

    await close_pool()

    print(f"\n✓ Seeded {total_programs} programs with {total_requirements} requirements")
    logger.info(
        "seed_singapore_cs_programs_complete",
        programs=total_programs,
        requirements=total_requirements,
    )


if __name__ == "__main__":
    asyncio.run(seed_programs())
