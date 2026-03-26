"""Seed the database with top 50 universities for initial crawling."""

import sys
import uuid
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import settings

load_dotenv(ROOT_DIR / ".env")


def get_connection():
    return mysql.connector.connect(
        host=settings.get_db_host(),
        port=settings.get_db_port(),
        database=settings.get_db_name(),
        user=settings.get_db_user(),
        password=settings.get_db_password(),
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )


UNIVERSITIES = [
    ("Massachusetts Institute of Technology", "United States", 1, "https://www.mit.edu", "https://www.mit.edu/education/"),
    ("University of Cambridge", "United Kingdom", 2, "https://www.cam.ac.uk", "https://www.cam.ac.uk/courses"),
    ("University of Oxford", "United Kingdom", 3, "https://www.ox.ac.uk", "https://www.ox.ac.uk/admissions/graduate"),
    ("Harvard University", "United States", 4, "https://www.harvard.edu", "https://www.harvard.edu/programs"),
    ("Stanford University", "United States", 5, "https://www.stanford.edu", "https://www.stanford.edu/academics"),
    ("California Institute of Technology", "United States", 6, "https://www.caltech.edu", "https://www.caltech.edu/academics"),
    ("Imperial College London", "United Kingdom", 7, "https://www.imperial.ac.uk", "https://www.imperial.ac.uk/study/courses"),
    ("ETH Zurich", "Switzerland", 8, "https://ethz.ch", "https://ethz.ch/en/studies/master.html"),
    ("University College London", "United Kingdom", 9, "https://www.ucl.ac.uk", "https://www.ucl.ac.uk/prospective-students"),
    ("University of Chicago", "United States", 10, "https://www.uchicago.edu", "https://www.uchicago.edu/programs"),
    ("National University of Singapore", "Singapore", 11, "https://www.nus.edu.sg", "https://www.nus.edu.sg/programmes"),
    ("University of Pennsylvania", "United States", 12, "https://www.upenn.edu", "https://www.upenn.edu/academics"),
    ("Cornell University", "United States", 13, "https://www.cornell.edu", "https://www.cornell.edu/academics"),
    ("University of Melbourne", "Australia", 14, "https://www.unimelb.edu.au", "https://study.unimelb.edu.au/find"),
    ("Princeton University", "United States", 15, "https://www.princeton.edu", "https://www.princeton.edu/academics"),
    ("Yale University", "United States", 16, "https://www.yale.edu", "https://www.yale.edu/academics"),
    ("Columbia University", "United States", 17, "https://www.columbia.edu", "https://www.columbia.edu/academics"),
    ("University of Toronto", "Canada", 18, "https://www.utoronto.ca", "https://www.utoronto.ca/programs"),
    ("University of Edinburgh", "United Kingdom", 19, "https://www.ed.ac.uk", "https://www.ed.ac.uk/studying/postgraduate"),
    ("Technical University of Munich", "Germany", 20, "https://www.tum.de", "https://www.tum.de/en/studies/degree-programs"),
    ("Johns Hopkins University", "United States", 21, "https://www.jhu.edu", "https://www.jhu.edu/academics"),
    ("Duke University", "United States", 22, "https://duke.edu", "https://duke.edu/academics"),
    ("Nanyang Technological University", "Singapore", 23, "https://www.ntu.edu.sg", "https://www.ntu.edu.sg/admissions/graduate"),
    ("University of Hong Kong", "Hong Kong", 24, "https://www.hku.hk", "https://www.hku.hk/programmes"),
    ("University of Manchester", "United Kingdom", 25, "https://www.manchester.ac.uk", "https://www.manchester.ac.uk/study/masters"),
    ("Northwestern University", "United States", 26, "https://www.northwestern.edu", "https://www.northwestern.edu/academics"),
    ("Peking University", "China", 27, "https://english.pku.edu.cn", "https://english.pku.edu.cn/Academics.htm"),
    ("University of Sydney", "Australia", 28, "https://www.sydney.edu.au", "https://www.sydney.edu.au/courses"),
    ("Tsinghua University", "China", 29, "https://www.tsinghua.edu.cn/en", "https://www.tsinghua.edu.cn/en/Academics.htm"),
    ("McGill University", "Canada", 30, "https://www.mcgill.ca", "https://www.mcgill.ca/study"),
    ("Australian National University", "Australia", 31, "https://www.anu.edu.au", "https://www.anu.edu.au/study"),
    ("University of British Columbia", "Canada", 32, "https://www.ubc.ca", "https://www.ubc.ca/programs"),
    ("Seoul National University", "South Korea", 33, "https://en.snu.ac.kr", "https://en.snu.ac.kr/academics"),
    ("KAIST", "South Korea", 34, "https://www.kaist.ac.kr/en", "https://www.kaist.ac.kr/en/html/academics"),
    ("University of Tokyo", "Japan", 35, "https://www.u-tokyo.ac.jp/en", "https://www.u-tokyo.ac.jp/en/academics"),
    ("University of Michigan", "United States", 36, "https://umich.edu", "https://umich.edu/academics"),
    ("New York University", "United States", 37, "https://www.nyu.edu", "https://www.nyu.edu/academics"),
    ("King's College London", "United Kingdom", 38, "https://www.kcl.ac.uk", "https://www.kcl.ac.uk/study/postgraduate"),
    ("London School of Economics", "United Kingdom", 39, "https://www.lse.ac.uk", "https://www.lse.ac.uk/programmes"),
    ("University of Waterloo", "Canada", 40, "https://uwaterloo.ca", "https://uwaterloo.ca/graduate-studies/programs"),
    ("Georgia Institute of Technology", "United States", 41, "https://www.gatech.edu", "https://www.gatech.edu/academics"),
    ("University of California Berkeley", "United States", 42, "https://www.berkeley.edu", "https://www.berkeley.edu/academics"),
    ("University of California Los Angeles", "United States", 43, "https://www.ucla.edu", "https://www.ucla.edu/academics"),
    ("Carnegie Mellon University", "United States", 44, "https://www.cmu.edu", "https://www.cmu.edu/academics"),
    ("University of Queensland", "Australia", 45, "https://www.uq.edu.au", "https://www.uq.edu.au/study/programs"),
    ("University of New South Wales", "Australia", 46, "https://www.unsw.edu.au", "https://www.unsw.edu.au/study"),
    ("University of Amsterdam", "Netherlands", 47, "https://www.uva.nl/en", "https://www.uva.nl/en/programmes"),
    ("Delft University of Technology", "Netherlands", 48, "https://www.tudelft.nl/en", "https://www.tudelft.nl/en/education/programmes"),
    ("EPFL", "Switzerland", 49, "https://www.epfl.ch/en", "https://www.epfl.ch/education/master"),
    ("University of Zurich", "Switzerland", 50, "https://www.uzh.ch/en", "https://www.uzh.ch/en/studies"),
]


def seed():
    conn = get_connection()
    cursor = conn.cursor()

    for name, country, ranking, website, programs_url in UNIVERSITIES:
        uid = str(uuid.uuid4())
        try:
            cursor.execute(
                """
                INSERT INTO universities (id, name, country, ranking, website, programs_page_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE ranking = VALUES(ranking), programs_page_url = VALUES(programs_page_url)
                """,
                (uid, name, country, ranking, website, programs_url),
            )
            print(f"  Seeded: {name} (rank #{ranking})")
        except Exception as exc:
            print(f"  Error seeding {name}: {exc}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n{len(UNIVERSITIES)} universities seeded successfully.")


if __name__ == "__main__":
    seed()
