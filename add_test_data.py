"""
add_test_data.py
─────────────────────────────────────────────────────────────
Inserts test verification codes into the live hostel.db
so new students can self-register at /register

Run with:  python add_test_data.py
─────────────────────────────────────────────────────────────
"""

import sqlite3
import os
import csv

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hostel.db')
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'students_data.csv')

# ── Test verification codes for new student self-registration ──────────────────
# The BEST APPROACH for bulk data like large student sheets is to use a CSV or Excel file.
# This script now automatically reads from 'students_data.csv' if it exists.
# If not, it falls back to this hard-coded list for easy testing.

FALLBACK_VERIFICATIONS = [
    # (verify_code,   name,             email,                    course,          year, gender)
    ('ADM2026005',   'Karan Mehta',    'karan@college.edu',   'B.Tech IT',     1, 'Male'),
    ('ADM2026006',   'Divya Rao',      'divya@college.edu',   'MBA',           1, 'Female'),
    ('ADM2026007',   'Rohit Bansal',   'rohit@college.edu',   'BBA',           2, 'Male'),
    ('ADM2026008',   'Anjali Mishra',  'anjali@college.edu',  'B.Sc CS',       1, 'Female'),
    ('ROLL2026A01',  'Dev Sharma',     'dev@college.edu',     'B.Tech Civil',  1, 'Male'),
    ('ROLL2026A02',  'Meera Nair',     'meera@college.edu',   'B.Sc Physics',  2, 'Female'),
]

def determine_student_type(verify_code, year):
    """
    Logic to dynamically decide if a student is a fresher or senior.
    - If Year is 1 -> Usually 'fresher' even if they have a ROLL number.
    - If Year > 1 -> Definitely 'senior'.
    """
    if int(year) == 1:
        return 'fresher'
    return 'senior'

def get_student_data():
    """Reads from CSV if available, prioritizing CSV as the best approach for large lists."""
    records = []
    if os.path.exists(CSV_PATH):
        print(f"📊 Found CSV file! Loading students from {CSV_PATH} ...")
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            # We assume CSV has columns: verify_code, student_type (optional), name, email, course, year, gender
            reader = csv.DictReader(f)
            for row in reader:
                v_code = row.get('verify_code', '').strip()
                if not v_code:
                    continue
                year = int(row.get('year', 1))
                
                # Check if CSV provided student_type, else auto-calculate
                s_type = row.get('student_type', '').strip()
                if not s_type:
                    s_type = determine_student_type(v_code, year)
                
                records.append((
                    v_code,
                    s_type.lower(),
                    row.get('name', '').strip(),
                    row.get('email', '').strip(),
                    row.get('course', '').strip(),
                    year,
                    row.get('gender', '').strip()
                ))
    else:
        print("ℹ️ No CSV file found. Using internal fallback list...")
        print("👉 TIP: For best results, keep large student sheets in 'students_data.csv'")
        for row in FALLBACK_VERIFICATIONS:
            v_code, name, email, course, year, gender = row
            s_type = determine_student_type(v_code, year)
            records.append((v_code, s_type, name, email, course, year, gender))
            
    return records


def main():
    print(f"\n📂 Database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Create the table if it does not exist (just in case)
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS student_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verify_code TEXT UNIQUE NOT NULL,
                student_type TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                course TEXT,
                year INTEGER,
                gender TEXT,
                is_used BOOLEAN DEFAULT 0
            )
        ''')
    except Exception as e:
        print(f"⚠️ Warning updating table: {e}")

    # Check existing verifications
    existing = []
    try:
        existing = [r['verify_code'] for r in c.execute("SELECT verify_code FROM student_verifications").fetchall()]
        print(f"\n📋 Already in student_verifications table: {len(existing)} records")
        if existing:
            for code in existing:
                print(f"   • {code}")
    except sqlite3.OperationalError:
        print("\n⚠️ Note: student_verifications table might not exist or lacks correct structure.")

    print(f"\n➕ Adding new verification codes...\n")

    added   = 0
    skipped = 0
    
    student_records = get_student_data()

    if not student_records:
        print("❌ No student data found to process.")
        return

    for row in student_records:
        code = row[0]
        s_type = row[1]
        name = row[2]
        course = row[4]
        year = row[5]
        
        if code in existing:
            print(f"   ⏩ SKIP  {code} — already exists")
            skipped += 1
        else:
            c.execute(
                '''INSERT INTO student_verifications
                   (verify_code, student_type, name, email, course, year, gender)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                row
            )
            print(f"   ✅ ADDED {code} ({s_type.upper()}) — {name} ({course} Year {year})")
            added += 1

    conn.commit()
    conn.close()

    print(f"\n{'─'*60}")
    print(f"✅ Done!  Added: {added}  |  Skipped: {skipped}")
    print(f"{'─'*60}")
    print(f"""
🎯 HOW TO TEST NEW STUDENT REGISTRATION:
─────────────────────────────────────────────────────────────
1. Open browser → http://localhost:5000/register

2. Choose "Fresher" or "Senior" based on the student's year,
   and enter their verification code.

3. Click Verify → Fill in username & password → Register

4. Go to http://localhost:5000/login
   → Use the credentials you just created
   → You will land on the STUDENT DASHBOARD 🎉

5. To verify in Admin panel:
   → Login as admin / admin123
   → Go to Students section → You'll see the new student!
─────────────────────────────────────────────────────────────
""")

if __name__ == '__main__':
    main()
