"""
create_localized_courses.py — 为各语言版「中文听说读写」创建 courses 表行。

语言位号（重要性顺序）：
  1=EN, 2=FR, 3=CN(skip), 4=JA, 5=KO, 6=ES, 7=VI, 8=PT,
  9=DE, 10=AR, 11=TH, 12=RU, 13=ID, 14=MS, 15=IT

_TO_CN 系列 course_id = 语言位号（1=EN_TO_CN, 2=FR_TO_CN, 4=JA_TO_CN, ...）
_TO_EN 系列 course_id = 100 + 语言位号（102=FR_TO_EN, 104=JA_TO_EN, ...）

已存在的 course_id 会跳过（不重复插入）。

用法（在 backend/ 目录下运行）：
    python database/create_localized_courses.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from database.connection import get_connection

# (course_id, category, name, target_language, source_language)
COURSES = [
    (1,  "EN_TO_CN", "Learn Chinese in English",                         "chinese", "english"),
    (2,  "FR_TO_CN", "Apprendre le chinois en français",                 "chinese", "français"),
    (4,  "JA_TO_CN", "日本語で中国語を学ぶ",                              "chinese", "日本語"),
    (5,  "KO_TO_CN", "한국어로 중국어 배우기",                            "chinese", "한국어"),
    (6,  "ES_TO_CN", "Aprende chino en español",                         "chinese", "español"),
    (7,  "VI_TO_CN", "Học tiếng Trung bằng tiếng Việt",                  "chinese", "tiếng việt"),
    (8,  "PT_TO_CN", "Aprenda chinês em português",                       "chinese", "português"),
    (9,  "DE_TO_CN", "Chinesisch lernen auf Deutsch",                    "chinese", "deutsch"),
    (10, "AR_TO_CN", "تعلم الصينية بالعربية",                            "chinese", "عربية"),
    (11, "TH_TO_CN", "เรียนภาษาจีนเป็นภาษาไทย",                         "chinese", "ภาษาไทย"),
    (12, "RU_TO_CN", "Учим китайский на русском",                         "chinese", "русский"),
    (13, "ID_TO_CN", "Belajar bahasa Mandarin dalam bahasa Indonesia",    "chinese", "bahasa indonesia"),
    (14, "MS_TO_CN", "Belajar bahasa Mandarin dalam bahasa Melayu",       "chinese", "bahasa melayu"),
    (15, "IT_TO_CN", "Impara il cinese in italiano",                      "chinese", "italiano"),
]


def main() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT course_id FROM courses")
    existing_ids = {row[0] for row in cur.fetchall()}

    created = skipped = 0
    for course_id, category, name, target_language, source_language in COURSES:
        if course_id in existing_ids:
            print(f"  ⏭️  已存在: {course_id} {category}")
            skipped += 1
            continue
        cur.execute(
            "INSERT INTO courses (course_id, name, category, target_language, source_language) VALUES (%s, %s, %s, %s, %s)",
            (course_id, name, category, target_language, source_language),
        )
        print(f"  ✅ 已创建: {course_id} {category} ({name})")
        created += 1

    cur.execute("SELECT setval('courses_course_id_seq', (SELECT MAX(course_id) FROM courses))")
    conn.commit()
    conn.close()
    print(f"\n完成：新建 {created} 个，跳过 {skipped} 个。")


if __name__ == "__main__":
    main()
