#!/usr/bin/env python3
"""
Generate QS World University Rankings 2026 JSON from raw data.

This script parses the QS rankings data and creates a JSON file
that can be used by the seed script.

Usage:
    python scripts/generate_qs_json.py
"""

import json
import re
from pathlib import Path


def parse_rank_display(rank_str: str) -> int:
    """Convert rank display string to numeric position.
    
    Examples:
        "1" -> 1
        "701-710" -> 701
        "1001-1200" -> 1001
        "1401+" -> 1401
    """
    rank_str = rank_str.strip()
    
    if rank_str.endswith("+"):
        return int(rank_str[:-1])
    
    if "-" in rank_str:
        return int(rank_str.split("-")[0])
    
    return int(rank_str)


def parse_score(score_str: str | None) -> float | None:
    """Parse a score string to float, handling empty values."""
    if not score_str or score_str.strip() == "" or score_str.strip() == "-":
        return None
    try:
        return float(score_str.strip())
    except ValueError:
        return None


QS_RANKINGS_2026_RAW = """1	Massachusetts Institute of Technology (MIT)	United States	100	100	100	100	100	100	96	99.2	91.7	100
2	Imperial College London	United Kingdom	98.3	97.5	99.9	100	100	100	97.6	99.7	96.3	97.5
3	University of Oxford	United Kingdom	100	100	100	91.3	99	98.9	96.7	99.4	95.4	96.9
4	Harvard University	United States	100	100	100	99.7	74.4	89.7	88.3	100	93.4	96.8
5	University of Cambridge	United Kingdom	100	100	100	93	97.7	97	97.5	97.9	96.4	96.7
6	Stanford University	United States	100	100	100	99.3	64.6	76.1	94.6	99.7	94.5	95.4
7	ETH Zurich	Switzerland	99	98	77.4	99.6	99.6	97.6	99.2	81.8	99.9	94.8
8	National University of Singapore (NUS)	Singapore	98.5	99.3	100	68	100	95.3	88.6	94.7	94.5	93.6
9	UCL	United Kingdom	99.5	94.6	99.5	71.7	99.4	100	95.3	93.2	94.3	93.3
10	California Institute of Technology (Caltech)	United States	90.9	82.1	100	100	81.8	93.1	91.9	93.5	94.7	92.9
11	University of Pennsylvania	United States	96.2	98.9	95	99.9	41.1	57	92.1	99.7	96.9	92.6
12	University of California, Berkeley (UCB)	United States	99.8	99.5	85.1	92.3	52.2	52.4	97.9	91.7	93.7	91.5
13	University of Melbourne	Australia	99.2	98.3	66.6	72.4	100	100	91.9	82	97.2	91.4
14	Peking University	China (Mainland)	99.5	97.9	100	66.6	66.7	37	92.4	79.9	97.4	90.7
15	Nanyang Technological University, Singapore (NTU)	Singapore	91.5	96.2	100	95.3	80.2	81.9	83	95.7	91.7	90.6
16	Cornell University	United States	93.9	96.6	85.7	96.6	59.2	67.1	97.6	94.4	92.5	90.1
17	The University of Hong Kong	Hong Kong SAR	96.8	93.7	100	63.3	97.9	91	90.9	85.6	83.7	90
18	University of Sydney	Australia	98.2	96.7	51.4	69.2	100	100	94.7	86.7	95.9	89.8
19	Tsinghua University	China (Mainland)	98.4	99.7	100	93.9	30.4	28.4	94.4	84.2	95.9	89.7
20	Princeton University	United States	99.5	89.6	100	99.4	45.6	66.9	93.6	84.9	91.7	89.1
21	Yale University	United States	99.3	98.4	91.7	81.7	58.2	65.9	94.5	92.5	91.3	89
22	Université PSL	France	98.5	59.1	100	98.3	79.1	81.3	88.4	71.7	95.4	88.9
23	University of New South Wales (UNSW Sydney)	Australia	91.1	95.9	35.5	84.5	100	100	92	82.9	97.9	88.6
24	University of Toronto	Canada	98.9	98.9	78.1	51.9	90.9	80.9	97.2	81.7	92.2	88.5
25	EPFL	Switzerland	83.7	77.3	100	99.4	99.7	93.5	92.6	76.6	99.7	88.3
26	University of Edinburgh	United Kingdom	97.8	88.7	52.7	56.9	97.7	97.5	98.6	86.3	92.5	87.6
27	Technical University of Munich	Germany	92.9	98.3	97.7	86.1	54.9	51	99.9	74.7	93.5	87.4
28	McGill University	Canada	95.3	86.7	78.1	67.6	97.9	93.9	86.9	85.1	88.2	86.5
29	University of Tokyo	Japan	100	94.9	99.9	60	60.5	30.9	91.4	73.6	92.4	86.3
30	University of California, Los Angeles (UCLA)	United States	98.8	99.1	41.9	77.2	42.7	44.3	98.7	90.7	92.7	86
31=	Columbia University	United States	98.9	97.7	48	64.9	64.4	75.9	96	94.9	87.6	85.5
31=	University of Michigan-Ann Arbor	United States	92.9	96.2	62.7	74.5	52.5	59.3	99.4	88.9	94.6	85.5
33	The Chinese University of Hong Kong (CUHK)	Hong Kong SAR	81.7	71.6	100	78.9	89.7	92	83.7	89.9	85	85.4
34	Johns Hopkins University	United States	83.9	79.6	70.3	100	52.8	61.9	91.5	98.3	92.9	85.3
35	University of Queensland	Australia	90.7	86.5	39.5	71.1	100	100	94.9	77.5	96.1	85.2
36	Seoul National University	South Korea	96.8	98	99.8	60.2	37.1	32.7	86.5	78.2	93.1	85.1
37	The University of Manchester	United Kingdom	95.9	93.9	39.9	52.5	95.9	96	96.5	84.8	93.1	84.8
38	King's College London	United Kingdom	90	81.3	69.2	59.3	100	100	89.5	90.4	92.3	84.7
39	Northwestern University	United States	88.6	93.4	57.1	81.3	52	53.7	96.2	96	90.9	84.3
40	Monash University	Australia	85.5	89.6	30	70.3	100	100	95.9	81.7	97.9	84.2
41	London School of Economics and Political Science (LSE)	United Kingdom	93.2	99.9	54.2	44.7	97.9	96.5	95.3	91.9	57.7	84.1
42	The Hong Kong University of Science and Technology	Hong Kong SAR	66.7	71.6	100	99.5	90.6	93.8	76.9	82.7	91	84
43	The University of Auckland	New Zealand	89.7	87	45.2	41.9	99.9	99.9	86.1	66.9	95.9	81
44	KAIST - Korea Advanced Institute of Science & Technology	South Korea	70.3	79.4	100	97.1	41.3	46.2	74.6	91.1	92	80.5
45	Kyoto University	Japan	95.1	77.2	89.9	59.7	33.2	15.2	87.9	71.7	93.1	80.4
46=	Duke University	United States	80.9	79.6	66.7	88.2	53	68.1	91.7	93.9	86.3	79.6
46=	The Hong Kong Polytechnic University	Hong Kong SAR	66.1	76.1	100	98.5	59.2	70.7	80.2	84.5	78.4	79.6
48	Zhejiang University	China (Mainland)	82.7	78.3	100	94.9	18.9	14.6	84.3	69.5	95.6	79.5
49=	New York University (NYU)	United States	90.9	96.3	35.7	56.7	56.7	70.4	94.1	91.9	85.4	79.3
49=	University of British Columbia	Canada	91.5	93.1	39	50.7	91.5	77.9	95.7	69	92.7	79.3
51	Fudan University	China (Mainland)	88.6	83.9	100	58.6	32.9	31.5	85.5	75.9	85.1	78.2
52	University of California, San Diego (UCSD)	United States	72.7	70.9	37.9	99.2	56.6	59.6	96.9	88.9	91.8	77.8
53	University of Amsterdam	Netherlands	82.9	68.7	43.7	64.2	86.7	79.6	93.7	68.7	94.9	76.6
54	Shanghai Jiao Tong University	China (Mainland)	80	77.9	100	90.7	14.2	12.5	82.6	72.5	93.9	76.3
55	ANU (Australian National University)	Australia	89.9	79.7	20.7	60.9	94	96.9	93.5	66.5	92.9	76.2
56	University of Warwick	United Kingdom	75.9	79.7	32.6	57.5	93.9	91.7	89.8	87.9	87.1	76
57	KU Leuven	Belgium	77.5	59.5	63.1	67	80.5	94.5	89.7	70.7	97.7	75.8
58	City University of Hong Kong	Hong Kong SAR	52.7	60.9	100	100	74.9	88.5	69.7	79.9	83.7	75.5
59	Institut Polytechnique de Paris	France	67.9	66.4	87.4	81.3	78.2	81.9	76.9	72	95.5	75.4
60=	University of Washington	United States	80.3	77.6	21.5	84.5	36.9	38.3	98.9	79.2	92.9	74.5
60=	University of Wisconsin-Madison	United States	77.9	66	46.1	83.8	30.9	30.7	96.8	75.6	97.4	74.5
62	National Taiwan University (NTU)	Taiwan	90.7	79.2	99.6	51.7	23.4	20.2	83.5	60.7	87.7	74.4
63	University of Bristol	United Kingdom	77.9	68.9	36.3	60	84.9	87.9	89.7	76.9	92.2	73.9
64	Sorbonne University	France	80.3	54.3	86.7	55.3	72.7	67.9	86.1	59.3	96.7	73.6
65	Delft University of Technology	Netherlands	71.9	81.1	51.9	72.9	60.1	60.3	89.7	77	96	73.4
66	University of Glasgow	United Kingdom	78.3	67.4	40	49.7	92.7	91.2	86.9	77.1	89.9	73.2
67	Brown University	United States	74.2	60.9	54.4	86.6	47.7	71.7	81.2	91.2	85.5	73
68	Ludwig-Maximilians-Universität München	Germany	89.7	71.1	77.6	54	58.5	53.2	94.7	56.3	82.5	72.7
69	Yonsei University	South Korea	70.9	87.9	98.2	53.5	26.9	28.2	78.7	80.2	79.3	72
70	University of Texas at Austin	United States	81.2	87.4	35.1	62.3	37.2	37.7	92.9	79.9	93.2	71.9
71	Korea University	South Korea	69	89.9	90.1	45.7	28.9	28.2	75.3	84.9	79.3	71.4
72=	The University of Sheffield	United Kingdom	70.7	68.4	34.5	46.4	93.7	90.7	86.9	74.9	92.7	71.2
72=	Tokyo Institute of Technology (Tokyo Tech)	Japan	56.5	71.6	99.9	83.5	42	40.2	71.1	73	90.6	71.2
74	University of Illinois Urbana-Champaign	United States	74.2	83.2	26	79.5	43.5	38.9	97.9	76.2	90.9	71.1
75	Universidad de Buenos Aires (UBA)	Argentina	92.8	91.6	97.9	1.4	6.7	15.9	63.7	52.8	85.5	71
76	University of Southampton	United Kingdom	64.3	55.8	30.9	58.6	93.2	94.9	87.2	72.3	94.1	70.9
77	Durham University	United Kingdom	65.3	62.9	41.4	45.7	92.6	88.4	82.9	85.9	87.7	70.7
78	University of Birmingham	United Kingdom	72.2	71.6	32.7	50.7	86.4	85.7	90.4	72.9	91.2	70.6
79	University of Leeds	United Kingdom	73.1	69.4	33.1	43.3	88.5	88.9	90.7	70.9	92.1	70.3
80	University of Zurich	Switzerland	67.3	55.5	34.5	75.9	79.3	88.7	86.4	65.9	98.7	70
81	University of Nottingham	United Kingdom	67.7	66	29.2	46.9	91.5	91.9	88.2	71.4	89.2	69.4
82=	Georgia Institute of Technology (Georgia Tech)	United States	62.3	85.4	30.1	81.9	41	41.5	92	82.9	86.9	69.3
82=	Trinity College Dublin, The University of Dublin	Ireland	74.5	71.5	36	35.7	90.7	87.5	82.7	78	88.1	69.3
84	Universiti Malaya (UM)	Malaysia	66.7	86.9	85.7	31.9	39.9	42.9	62	75.9	91.5	68.9
85	Ruprecht-Karls-Universität Heidelberg	Germany	80.9	51.7	49.9	69.1	51.7	53.3	84.9	54.7	93.9	68.8
86	Carnegie Mellon University	United States	63.7	74	41.9	90.1	43.9	55.2	76.9	87.3	83.2	68.6
87	University of St Andrews	United Kingdom	65.1	48.5	34.7	49.6	98.7	98.1	75.2	74.7	82.1	68.1
88	The University of Adelaide	Australia	66.1	61	13.7	57.9	95.7	99.4	82.7	65.7	92.6	67.8
89	University of Copenhagen	Denmark	78.7	43	30.9	80.4	49.1	73.9	90.7	61.7	93.5	67.6
90	RWTH Aachen University	Germany	58.2	80.7	59.1	63.3	56.1	56.7	86.6	56.4	94.2	67.5
91	Universidad Nacional Autónoma de México (UNAM)	Mexico	97.9	92.5	100	3.6	4.6	5	64.9	48.9	90.2	67.4
92=	The University of Western Australia	Australia	62.3	59.5	7.3	67.5	85.3	94.4	86.7	67.3	94.9	67.3
92=	University of Oslo	Norway	60.1	33.7	25.5	60.1	82.2	94.1	81.3	63.6	99.9	67.3
94	KTH Royal Institute of Technology	Sweden	53	59.7	51.9	65.4	71.3	81.5	79	72.6	96.8	67.2
95	Pohang University of Science and Technology (POSTECH)	South Korea	35.1	48.3	100	100	47.2	53.2	54.2	75.9	84.7	67
96	Lund University	Sweden	68.7	44.8	29	56.7	83.4	93.4	88.2	59.2	96.6	66.8
97	Lomonosov Moscow State University	Russia	87.5	79.9	99.5	10.4	23.5	17.9	76.4	41.2	87.2	66.6
98	University of Science and Technology of China	China (Mainland)	49.2	48.7	100	99.3	12.2	16.9	74.5	55.5	92.1	66.2
99	University of Alberta	Canada	60.3	59.7	22.2	64.9	73.7	74.9	87.9	66.5	89.9	66.1
100	Utrecht University	Netherlands	65.7	45.5	28.4	64	58.5	71.6	93.7	57.9	92.9	65.3"""


def generate_qs_json():
    """Generate QS rankings JSON from raw data."""
    institutions = []
    
    for line in QS_RANKINGS_2026_RAW.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        
        rank_display = parts[0].replace("=", "").strip()
        name = parts[1].strip()
        country = parts[2].strip()
        overall_score = parse_score(parts[3]) if len(parts) > 3 else None
        
        indicators = {}
        if len(parts) > 4:
            indicators["academic_reputation"] = parse_score(parts[4])
        if len(parts) > 5:
            indicators["employer_reputation"] = parse_score(parts[5])
        if len(parts) > 6:
            indicators["faculty_student_ratio"] = parse_score(parts[6])
        if len(parts) > 7:
            indicators["citations_per_faculty"] = parse_score(parts[7])
        if len(parts) > 8:
            indicators["international_faculty_ratio"] = parse_score(parts[8])
        if len(parts) > 9:
            indicators["international_students_ratio"] = parse_score(parts[9])
        if len(parts) > 10:
            indicators["international_research_network"] = parse_score(parts[10])
        if len(parts) > 11:
            indicators["employment_outcomes"] = parse_score(parts[11])
        if len(parts) > 12:
            indicators["sustainability"] = parse_score(parts[12])
        
        institution = {
            "rank_display": rank_display,
            "rank_position": parse_rank_display(rank_display),
            "name": name,
            "country": country,
            "overall_score": overall_score,
            "indicators": {k: v for k, v in indicators.items() if v is not None},
        }
        institutions.append(institution)
    
    output = {
        "ranking_source": "qs_world",
        "ranking_year": 2026,
        "source_url": "https://www.topuniversities.com/world-university-rankings/2026",
        "institutions": institutions,
    }
    
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "qs_world_rankings_2026.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(institutions)} institutions to {output_file}")


if __name__ == "__main__":
    generate_qs_json()
