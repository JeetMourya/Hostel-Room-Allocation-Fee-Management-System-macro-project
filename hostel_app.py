
"""
HOSTEL MANAGEMENT SYSTEM — Real World Edition
Python + SQLite + Flask
Features: Students, Rooms, Allocations, Fees, Complaints, Notices, Dashboard Charts
"""

import sqlite3
import datetime
import random
import string
import os
import hashlib
from functools import wraps
from flask import Flask, jsonify, request, Response, session, redirect
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'hostel_secret_2026_xyz'
CORS(app)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hostel.db')



def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    c.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        username   TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        role       TEXT DEFAULT "student",
        student_id INTEGER,
        name       TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS students (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id    TEXT UNIQUE NOT NULL,
        name          TEXT NOT NULL,
        email         TEXT UNIQUE NOT NULL,
        phone         TEXT,
        gender        TEXT CHECK(gender IN ("Male","Female","Other")),
        dob           DATE,
        address       TEXT,
        guardian_name TEXT,
        guardian_phone TEXT,
        course        TEXT,
        year          INTEGER,
        status        TEXT DEFAULT "Active",
        photo_url     TEXT,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS rooms (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        room_no    TEXT UNIQUE NOT NULL,
        block      TEXT NOT NULL,
        floor      INTEGER NOT NULL DEFAULT 1,
        type       TEXT DEFAULT "Single",
        capacity   INTEGER NOT NULL DEFAULT 1,
        occupied   INTEGER DEFAULT 0,
        status     TEXT DEFAULT "Available",
        rent       REAL NOT NULL,
        deposit    REAL DEFAULT 0,
        amenities  TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS allocations (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id     INTEGER NOT NULL,
        room_id        INTEGER NOT NULL,
        allocated_date DATE NOT NULL,
        vacate_date    DATE,
        expected_vacate DATE,
        status         TEXT DEFAULT "Active",
        remarks        TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (room_id)    REFERENCES rooms(id)
    );

    CREATE TABLE IF NOT EXISTS fees (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id   INTEGER NOT NULL,
        month        TEXT,
        amount       REAL NOT NULL,
        discount     REAL DEFAULT 0,
        fine         REAL DEFAULT 0,
        due_date     DATE NOT NULL,
        paid_date    DATE,
        status       TEXT DEFAULT "Pending",
        payment_mode TEXT,
        receipt_no   TEXT UNIQUE,
        remarks      TEXT,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS complaints (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER NOT NULL,
        category    TEXT NOT NULL,
        subject     TEXT NOT NULL,
        description TEXT,
        status      TEXT DEFAULT "Open",
        priority    TEXT DEFAULT "Medium",
        resolved_at TIMESTAMP,
        remarks     TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS notices (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT NOT NULL,
        content    TEXT NOT NULL,
        category   TEXT DEFAULT "General",
        priority   TEXT DEFAULT "Normal",
        active     INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at DATE
    );

    CREATE TABLE IF NOT EXISTS visitors (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER NOT NULL,
        visitor_name TEXT NOT NULL,
        relation    TEXT,
        phone       TEXT,
        purpose     TEXT,
        check_in    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        check_out   TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS student_verifications (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        verify_code   TEXT UNIQUE NOT NULL,
        student_type  TEXT NOT NULL DEFAULT 'fresher',
        name          TEXT NOT NULL,
        email         TEXT,
        course        TEXT,
        year          INTEGER DEFAULT 1,
        gender        TEXT DEFAULT 'Male',
        is_registered INTEGER DEFAULT 0,
        registered_at TIMESTAMP,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Seed users
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        def h(p): return hashlib.sha256(p.encode()).hexdigest()
        c.execute("INSERT INTO users (username,password,role,name) VALUES (?,?,?,?)",('admin', h('admin123'),'admin','Administrator'))
        c.execute("INSERT INTO users (username,password,role,name) VALUES (?,?,?,?)",('warden', h('warden123'),'admin','Warden'))
        c.execute("INSERT INTO users (username,password,role,student_id,name) VALUES (?,?,?,?,?)",('rahul', h('rahul123'),'student',1,'Rahul Sharma'))
        c.execute("INSERT INTO users (username,password,role,student_id,name) VALUES (?,?,?,?,?)",('priya', h('priya123'),'student',2,'Priya Singh'))
        c.execute("INSERT INTO users (username,password,role,student_id,name) VALUES (?,?,?,?,?)",('amit', h('amit123'),'student',3,'Amit Kumar'))

    # Seed data if empty
    c.execute("SELECT COUNT(*) FROM rooms")
    if c.fetchone()[0] == 0:
        rooms = [
            ('101', 'A', 1, 'Single',  1, 4500,  5000, 'Fan, Cupboard'),
            ('102', 'A', 1, 'Double',  2, 3800,  4000, 'Fan, Cupboard, Table'),
            ('103', 'A', 1, 'Triple',  3, 3200,  3500, 'Fan, Cupboard'),
            ('201', 'A', 2, 'Single',  1, 5500,  6000, 'AC, Wi-Fi, Attached Bath'),
            ('202', 'A', 2, 'Double',  2, 4800,  5000, 'AC, Wi-Fi, Cupboard'),
            ('203', 'A', 2, 'Triple',  3, 4200,  4500, 'AC, Wi-Fi'),
            ('301', 'B', 1, 'Single',  1, 4000,  4500, 'Fan, Wi-Fi'),
            ('302', 'B', 1, 'Double',  2, 3500,  4000, 'Fan, Wi-Fi, Table'),
            ('303', 'B', 2, 'Single',  1, 5000,  5500, 'AC, Geyser, Attached Bath'),
            ('304', 'B', 2, 'Double',  2, 4500,  5000, 'AC, Geyser, Wi-Fi'),
        ]
        c.executemany('''INSERT INTO rooms (room_no,block,floor,type,capacity,rent,deposit,amenities)
                         VALUES (?,?,?,?,?,?,?,?)''', rooms)

        students = [
            ('S001','Rahul Sharma','rahul@college.edu','9876543210','Male','2003-05-12','123 Main St, Delhi','Suresh Sharma','9988776655','B.Tech CSE',3),
            ('S002','Priya Singh','priya@college.edu','9876543211','Female','2004-08-20','45 Park Ave, Mumbai','Rajesh Singh','9988776644','B.Tech ECE',2),
            ('S003','Amit Kumar','amit@college.edu','9876543212','Male','2002-11-03','78 Lake Rd, Pune','Mohan Kumar','9988776633','B.Tech ME',4),
            ('S004','Sneha Patel','sneha@college.edu','9876543213','Female','2005-02-28','22 Hill St, Ahmedabad','Vikram Patel','9988776622','BCA',1),
        ]
        c.executemany('''INSERT INTO students (student_id,name,email,phone,gender,dob,address,guardian_name,guardian_phone,course,year)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)''', students)

        today = datetime.date.today().isoformat()
        c.execute("INSERT INTO allocations (student_id,room_id,allocated_date,status) VALUES (1,2,?,?)", (today,'Active'))
        c.execute("UPDATE rooms SET occupied=1 WHERE id=2")
        c.execute("INSERT INTO allocations (student_id,room_id,allocated_date,status) VALUES (2,5,?,?)", (today,'Active'))
        c.execute("UPDATE rooms SET occupied=1 WHERE id=5")

        # Seed fees
        for sid in [1,2,3,4]:
            month = datetime.date.today().strftime('%B %Y')
            due   = datetime.date.today().replace(day=10).isoformat()
            receipt = 'RCP' + ''.join(random.choices(string.digits, k=8))
            c.execute('''INSERT INTO fees (student_id,month,amount,due_date,status,receipt_no)
                         VALUES (?,?,?,?,?,?)''', (sid, month, 4500, due, 'Pending', receipt))

        c.execute('''INSERT INTO notices (title,content,category,priority,expires_at) VALUES
            ("Hostel Fee Due","Please pay your hostel fee before 10th of every month.","Fee","High","2026-12-31"),
            ("Water Supply Maintenance","Water supply will be shut on 28 Feb from 10AM–2PM.","Maintenance","Normal","2026-03-01"),
            ("Visitors Policy","Visitors allowed only between 9AM–7PM on working days.","General","Normal","2026-12-31")
        ''')

    # Seed pre-approved verifications for self-registration
    c.execute("SELECT COUNT(*) FROM student_verifications")
    if c.fetchone()[0] == 0:
        verifs = [
            ('ADM2026001', 'fresher',  'Ravi Verma',    'ravi@college.edu',    'B.Tech CSE', 1, 'Male'),
            ('ADM2026002', 'fresher',  'Sakshi Jain',   'sakshi@college.edu',  'B.Tech ECE', 1, 'Female'),
            ('ADM2026003', 'fresher',  'Arjun Mehta',   'arjun@college.edu',   'BCA',        1, 'Male'),
            ('ADM2026004', 'fresher',  'Neha Gupta',    'neha@college.edu',    'B.Sc IT',    1, 'Female'),
            ('S004',       'existing', 'Sneha Patel',   'sneha@college.edu',   'BCA',        1, 'Female'),
        ]
        c.executemany('''INSERT INTO student_verifications
            (verify_code,student_type,name,email,course,year,gender) VALUES (?,?,?,?,?,?,?)''', verifs)

    conn.commit()
    conn.close()
    print("✅ Database ready!")

init_database()

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def gen_receipt():
    return 'RCP' + datetime.datetime.now().strftime('%Y%m%d') + ''.join(random.choices(string.digits, k=4))

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ─── API: DASHBOARD ──────────────────────────────────────────────────────────

@app.route('/api/stats')
def api_stats():
    conn = get_db()
    c = conn.cursor()
    stats = {
        'total_rooms':     c.execute("SELECT COUNT(*) FROM rooms").fetchone()[0],
        'total_students':  c.execute("SELECT COUNT(*) FROM students WHERE status='Active'").fetchone()[0],
        'total_capacity':  c.execute("SELECT COALESCE(SUM(capacity),0) FROM rooms").fetchone()[0],
        'total_occupied':  c.execute("SELECT COALESCE(SUM(occupied),0) FROM rooms").fetchone()[0],
        'available_rooms': c.execute("SELECT COUNT(*) FROM rooms WHERE occupied < capacity AND status='Available'").fetchone()[0],
        'pending_fees':    c.execute("SELECT COALESCE(SUM(amount+fine-discount),0) FROM fees WHERE status='Pending'").fetchone()[0],
        'collected_fees':  c.execute("SELECT COALESCE(SUM(amount),0) FROM fees WHERE status='Paid'").fetchone()[0],
        'open_complaints': c.execute("SELECT COUNT(*) FROM complaints WHERE status='Open'").fetchone()[0],
        'active_notices':  c.execute("SELECT COUNT(*) FROM notices WHERE active=1").fetchone()[0],
        'recent_students': rows_to_list(c.execute("SELECT id,student_id,name,course,year,created_at FROM students ORDER BY created_at DESC LIMIT 6").fetchall()),
        'available_room_list': rows_to_list(c.execute("SELECT id,room_no,block,floor,type,capacity,occupied,rent FROM rooms WHERE occupied<capacity AND status='Available' ORDER BY block,room_no LIMIT 6").fetchall()),
        'room_type_stats': rows_to_list(c.execute("SELECT type, COUNT(*) as count, SUM(occupied) as occupied, SUM(capacity) as capacity FROM rooms GROUP BY type").fetchall()),
        'fee_months': rows_to_list(c.execute("SELECT month, SUM(CASE WHEN status='Paid' THEN amount ELSE 0 END) as paid, SUM(CASE WHEN status='Pending' THEN amount ELSE 0 END) as pending FROM fees GROUP BY month ORDER BY created_at DESC LIMIT 6").fetchall()),
    }
    conn.close()
    return jsonify(stats)

# ─── API: STUDENTS ────────────────────────────────────────────────────────────

@app.route('/api/students', methods=['GET'])
def api_get_students():
    q = request.args.get('q','')
    status = request.args.get('status','')
    conn = get_db()
    sql = "SELECT * FROM students WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR student_id LIKE ? OR email LIKE ? OR phone LIKE ?)"
        params += [f'%{q}%']*4
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    rows = rows_to_list(conn.execute(sql, params).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/students/<int:sid>', methods=['GET'])
def api_get_student(sid):
    conn = get_db()
    s = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    if not s:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    student = dict(s)
    student['allocation'] = dict(conn.execute("""
        SELECT a.*,r.room_no,r.block,r.floor,r.rent FROM allocations a
        JOIN rooms r ON r.id=a.room_id WHERE a.student_id=? AND a.status='Active'
    """, (sid,)).fetchone() or {})
    student['fees']      = rows_to_list(conn.execute("SELECT * FROM fees WHERE student_id=? ORDER BY due_date DESC", (sid,)).fetchall())
    student['complaints']= rows_to_list(conn.execute("SELECT * FROM complaints WHERE student_id=? ORDER BY created_at DESC", (sid,)).fetchall())
    conn.close()
    return jsonify(student)

@app.route('/api/students', methods=['POST'])
def api_add_student():
    d = request.json
    required = ['student_id','name','email']
    for f in required:
        if not d.get(f):
            return jsonify({'error': f'{f} is required'}), 400
    conn = get_db()
    try:
        conn.execute('''INSERT INTO students
            (student_id,name,email,phone,gender,dob,address,guardian_name,guardian_phone,course,year)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (d['student_id'],d['name'],d['email'],d.get('phone'),d.get('gender','Male'),
             d.get('dob'),d.get('address'),d.get('guardian_name'),d.get('guardian_phone'),
             d.get('course'),d.get('year')))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Student added successfully'}), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'error': 'Student ID or Email already exists'}), 409

@app.route('/api/students/<int:sid>', methods=['PUT'])
def api_update_student(sid):
    d = request.json
    conn = get_db()
    conn.execute('''UPDATE students SET name=?,email=?,phone=?,gender=?,dob=?,address=?,
        guardian_name=?,guardian_phone=?,course=?,year=?,status=? WHERE id=?''',
        (d.get('name'),d.get('email'),d.get('phone'),d.get('gender'),d.get('dob'),
         d.get('address'),d.get('guardian_name'),d.get('guardian_phone'),
         d.get('course'),d.get('year'),d.get('status','Active'),sid))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Student updated'})

@app.route('/api/students/<int:sid>', methods=['DELETE'])
def api_delete_student(sid):
    conn = get_db()
    conn.execute("UPDATE students SET status='Inactive' WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Student deactivated'})

# ─── API: ROOMS ───────────────────────────────────────────────────────────────

@app.route('/api/rooms', methods=['GET'])
def api_get_rooms():
    q      = request.args.get('q','')
    status = request.args.get('status','')
    block  = request.args.get('block','')
    conn   = get_db()
    sql    = "SELECT * FROM rooms WHERE 1=1"
    params = []
    if q:
        sql += " AND (room_no LIKE ? OR block LIKE ? OR type LIKE ?)"
        params += [f'%{q}%']*3
    if status:
        sql += " AND status=?"
        params.append(status)
    if block:
        sql += " AND block=?"
        params.append(block)
    sql += " ORDER BY block, floor, room_no"
    rows = rows_to_list(conn.execute(sql, params).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/rooms/available', methods=['GET'])
def api_available_rooms():
    conn  = get_db()
    rows  = rows_to_list(conn.execute(
        "SELECT * FROM rooms WHERE occupied<capacity AND status='Available' ORDER BY block,floor,room_no"
    ).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/rooms/<int:rid>', methods=['GET'])
def api_get_room(rid):
    conn = get_db()
    r = conn.execute("SELECT * FROM rooms WHERE id=?", (rid,)).fetchone()
    if not r:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    room = dict(r)
    room['occupants'] = rows_to_list(conn.execute("""
        SELECT a.id,a.allocated_date,a.expected_vacate,s.id as student_db_id,s.student_id,s.name,s.phone,s.course,s.year
        FROM allocations a JOIN students s ON s.id=a.student_id
        WHERE a.room_id=? AND a.status='Active'
    """, (rid,)).fetchall())
    conn.close()
    return jsonify(room)

@app.route('/api/rooms', methods=['POST'])
def api_add_room():
    d = request.json
    if not d.get('room_no') or not d.get('block') or not d.get('rent'):
        return jsonify({'error': 'room_no, block, rent are required'}), 400
    conn = get_db()
    try:
        conn.execute('''INSERT INTO rooms (room_no,block,floor,type,capacity,rent,deposit,amenities,description)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (d['room_no'],d['block'],d.get('floor',1),d.get('type','Single'),
             d.get('capacity',1),d['rent'],d.get('deposit',0),
             d.get('amenities',''),d.get('description','')))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Room added'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Room number already exists'}), 409

@app.route('/api/rooms/<int:rid>', methods=['PUT'])
def api_update_room(rid):
    d = request.json
    conn = get_db()
    conn.execute('''UPDATE rooms SET room_no=?,block=?,floor=?,type=?,capacity=?,
        rent=?,deposit=?,amenities=?,description=?,status=? WHERE id=?''',
        (d.get('room_no'),d.get('block'),d.get('floor',1),d.get('type','Single'),
         d.get('capacity',1),d.get('rent'),d.get('deposit',0),
         d.get('amenities'),d.get('description'),d.get('status','Available'),rid))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Room updated'})

@app.route('/api/rooms/<int:rid>', methods=['DELETE'])
def api_delete_room(rid):
    conn = get_db()
    active = conn.execute("SELECT COUNT(*) FROM allocations WHERE room_id=? AND status='Active'",(rid,)).fetchone()[0]
    if active:
        conn.close()
        return jsonify({'error': 'Cannot delete room with active occupants'}), 400
    conn.execute("UPDATE rooms SET status='Maintenance' WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Room moved to Maintenance'})

# ─── API: ALLOCATIONS ─────────────────────────────────────────────────────────

@app.route('/api/allocations', methods=['GET'])
def api_get_allocations():
    status = request.args.get('status','Active')
    conn = get_db()
    rows = rows_to_list(conn.execute("""
        SELECT a.*,s.student_id,s.name as student_name,s.phone,s.course,
               r.room_no,r.block,r.floor,r.type,r.rent
        FROM allocations a
        JOIN students s ON s.id=a.student_id
        JOIN rooms r ON r.id=a.room_id
        WHERE a.status=?
        ORDER BY a.allocated_date DESC
    """, (status,)).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/allocate', methods=['POST'])
def api_allocate():
    d = request.json
    student_id = d.get('student_id')
    room_id    = d.get('room_id')
    expected   = d.get('expected_vacate')
    if not student_id or not room_id:
        return jsonify({'error': 'student_id and room_id required'}), 400
    conn = get_db()
    # Check student already allocated
    existing = conn.execute(
        "SELECT id FROM allocations WHERE student_id=? AND status='Active'", (student_id,)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Student already has an active room allocation'}), 400
    room = conn.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()
    if not room:
        conn.close()
        return jsonify({'error': 'Room not found'}), 404
    if room['occupied'] >= room['capacity']:
        conn.close()
        return jsonify({'error': 'Room is at full capacity'}), 400
    today = datetime.date.today().isoformat()
    conn.execute('''INSERT INTO allocations (student_id,room_id,allocated_date,expected_vacate,status)
                    VALUES (?,?,?,?,'Active')''', (student_id, room_id, today, expected))
    conn.execute("UPDATE rooms SET occupied=occupied+1 WHERE id=?", (room_id,))
    conn.execute("""UPDATE rooms SET status=CASE WHEN occupied>=capacity THEN 'Full' ELSE 'Available' END WHERE id=?""", (room_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Room allocated successfully'})

@app.route('/api/vacate', methods=['POST'])
def api_vacate():
    d = request.json
    alloc_id = d.get('allocation_id')
    conn = get_db()
    alloc = conn.execute("SELECT * FROM allocations WHERE id=? AND status='Active'", (alloc_id,)).fetchone()
    if not alloc:
        conn.close()
        return jsonify({'error': 'Active allocation not found'}), 404
    today = datetime.date.today().isoformat()
    conn.execute("UPDATE allocations SET status='Vacated',vacate_date=?,remarks=? WHERE id=?",
                 (today, d.get('remarks',''), alloc_id))
    conn.execute("UPDATE rooms SET occupied=MAX(0,occupied-1) WHERE id=?", (alloc['room_id'],))
    conn.execute("UPDATE rooms SET status='Available' WHERE id=? AND status='Full'", (alloc['room_id'],))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Room vacated successfully'})

# ─── API: FEES ────────────────────────────────────────────────────────────────

@app.route('/api/fees', methods=['GET'])
def api_get_fees():
    status     = request.args.get('status','')
    student_id = request.args.get('student_id','')
    q          = request.args.get('q','')
    conn = get_db()
    sql = """SELECT f.*,s.name as student_name,s.student_id as s_id
             FROM fees f JOIN students s ON s.id=f.student_id WHERE 1=1"""
    params = []
    if status:
        sql += " AND f.status=?"; params.append(status)
    if student_id:
        sql += " AND f.student_id=?"; params.append(student_id)
    if q:
        sql += " AND (s.name LIKE ? OR s.student_id LIKE ? OR f.receipt_no LIKE ?)"
        params += [f'%{q}%']*3
    sql += " ORDER BY f.created_at DESC"
    rows = rows_to_list(conn.execute(sql, params).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/fees/generate', methods=['POST'])
def api_generate_fees():
    """Generate monthly fees for all active allocated students"""
    d     = request.json
    month = d.get('month', datetime.date.today().strftime('%B %Y'))
    due   = d.get('due_date', datetime.date.today().replace(day=10).isoformat())
    conn  = get_db()
    students = conn.execute("""
        SELECT DISTINCT a.student_id,r.rent FROM allocations a
        JOIN rooms r ON r.id=a.room_id WHERE a.status='Active'
    """).fetchall()
    count = 0
    for s in students:
        existing = conn.execute(
            "SELECT id FROM fees WHERE student_id=? AND month=?", (s['student_id'], month)
        ).fetchone()
        if not existing:
            receipt = gen_receipt()
            conn.execute('''INSERT INTO fees (student_id,month,amount,due_date,receipt_no)
                            VALUES (?,?,?,?,?)''', (s['student_id'], month, s['rent'], due, receipt))
            count += 1
    conn.commit()
    conn.close()
    return jsonify({'message': f'Generated {count} fee records for {month}'})

@app.route('/api/fees/pay', methods=['POST'])
def api_pay_fee():
    d = request.json
    fee_id = d.get('fee_id')
    conn = get_db()
    if fee_id:
        conn.execute('''UPDATE fees SET status='Paid',paid_date=date('now'),
            payment_mode=?,remarks=? WHERE id=?''',
            (d.get('payment_mode','Cash'), d.get('remarks',''), fee_id))
    else:
        receipt = gen_receipt()
        conn.execute('''INSERT INTO fees (student_id,month,amount,discount,fine,due_date,paid_date,status,payment_mode,receipt_no,remarks)
            VALUES (?,?,?,?,?,date('now'),date('now'),'Paid',?,?,?)''',
            (d['student_id'], d.get('month', datetime.date.today().strftime('%B %Y')),
             d['amount'], d.get('discount',0), d.get('fine',0),
             d.get('payment_mode','Cash'), receipt, d.get('remarks','')))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Payment recorded', 'receipt_no': d.get('receipt_no', receipt if not fee_id else '')})

@app.route('/api/fees/summary', methods=['GET'])
def api_fee_summary():
    student_id = request.args.get('student_id')
    conn = get_db()
    rows = rows_to_list(conn.execute("SELECT * FROM fees WHERE student_id=? ORDER BY due_date DESC", (student_id,)).fetchall())
    total   = sum(r['amount'] for r in rows)
    paid    = sum(r['amount'] for r in rows if r['status']=='Paid')
    pending = sum(r['amount'] for r in rows if r['status']=='Pending')
    conn.close()
    return jsonify({'records': rows, 'total': total, 'paid': paid, 'pending': pending})

# ─── API: COMPLAINTS ──────────────────────────────────────────────────────────

@app.route('/api/complaints', methods=['GET'])
def api_get_complaints():
    status     = request.args.get('status','')
    student_id = request.args.get('student_id','')
    conn = get_db()
    sql = """SELECT c.*,s.name as student_name,s.student_id as s_id
             FROM complaints c JOIN students s ON s.id=c.student_id WHERE 1=1"""
    params = []
    if status:
        sql += " AND c.status=?"; params.append(status)
    if student_id:
        sql += " AND c.student_id=?"; params.append(student_id)
    sql += " ORDER BY c.created_at DESC"
    rows = rows_to_list(conn.execute(sql, params).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/complaints', methods=['POST'])
def api_add_complaint():
    d = request.json
    conn = get_db()
    conn.execute('''INSERT INTO complaints (student_id,category,subject,description,priority)
                    VALUES (?,?,?,?,?)''',
        (d['student_id'], d['category'], d['subject'], d.get('description',''), d.get('priority','Medium')))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Complaint registered'}), 201

@app.route('/api/complaints/<int:cid>', methods=['PUT'])
def api_update_complaint(cid):
    d = request.json
    conn = get_db()
    resolved_at = datetime.datetime.now().isoformat() if d.get('status') == 'Resolved' else None
    conn.execute("UPDATE complaints SET status=?,remarks=?,resolved_at=? WHERE id=?",
                 (d.get('status'), d.get('remarks'), resolved_at, cid))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Complaint updated'})

# ─── API: NOTICES ─────────────────────────────────────────────────────────────

@app.route('/api/notices', methods=['GET'])
def api_get_notices():
    conn = get_db()
    rows = rows_to_list(conn.execute(
        "SELECT * FROM notices WHERE active=1 ORDER BY created_at DESC"
    ).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/notices', methods=['POST'])
def api_add_notice():
    d = request.json
    conn = get_db()
    conn.execute('''INSERT INTO notices (title,content,category,priority,expires_at)
                    VALUES (?,?,?,?,?)''',
        (d['title'], d['content'], d.get('category','General'), d.get('priority','Normal'), d.get('expires_at')))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Notice posted'}), 201

@app.route('/api/notices/<int:nid>', methods=['DELETE'])
def api_delete_notice(nid):
    conn = get_db()
    conn.execute("UPDATE notices SET active=0 WHERE id=?", (nid,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Notice removed'})

# ─── API: VISITORS ────────────────────────────────────────────────────────────

@app.route('/api/visitors', methods=['GET'])
def api_get_visitors():
    conn = get_db()
    rows = rows_to_list(conn.execute("""
        SELECT v.*,s.name as student_name,s.student_id as s_id FROM visitors v
        JOIN students s ON s.id=v.student_id ORDER BY v.check_in DESC LIMIT 50
    """).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/visitors', methods=['POST'])
def api_add_visitor():
    d = request.json
    conn = get_db()
    conn.execute('''INSERT INTO visitors (student_id,visitor_name,relation,phone,purpose)
                    VALUES (?,?,?,?,?)''',
        (d['student_id'], d['visitor_name'], d.get('relation'), d.get('phone'), d.get('purpose')))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Visitor checked in'}), 201

@app.route('/api/visitors/<int:vid>/checkout', methods=['POST'])
def api_visitor_checkout(vid):
    conn = get_db()
    conn.execute("UPDATE visitors SET check_out=CURRENT_TIMESTAMP WHERE id=?", (vid,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Visitor checked out'})

# ─── API: STUDENT VERIFICATIONS (ADMIN) ────────────────────────────────────────

@app.route('/api/verifications', methods=['GET'])
def api_get_verifications():
    conn = get_db()
    rows = rows_to_list(conn.execute("SELECT * FROM student_verifications ORDER BY created_at DESC").fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/verifications', methods=['POST'])
def api_add_verification():
    d = request.json
    if not d.get('verify_code') or not d.get('name'):
        return jsonify({'error': 'verify_code and name are required'}), 400
    conn = get_db()
    try:
        conn.execute('''INSERT INTO student_verifications
            (verify_code,student_type,name,email,course,year,gender) VALUES (?,?,?,?,?,?,?)''',
            (d['verify_code'], d.get('student_type','fresher'), d['name'],
             d.get('email'), d.get('course'), d.get('year',1), d.get('gender','Male')))
        conn.commit(); conn.close()
        return jsonify({'message': 'Verification record added'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Verify code already exists'}), 409

@app.route('/api/verifications/<int:vid>', methods=['DELETE'])
def api_delete_verification(vid):
    conn = get_db()
    conn.execute("DELETE FROM student_verifications WHERE id=? AND is_registered=0", (vid,))
    conn.commit(); conn.close()
    return jsonify({'message': 'Deleted'})

# ─── API: SELF-REGISTRATION (PUBLIC) ────────────────────────────────────────────

@app.route('/api/verify-identity', methods=['POST'])
def api_verify_identity():
    d    = request.json
    code = (d.get('verify_code') or '').strip()
    if not code:
        return jsonify({'error': 'Verification code is required'}), 400
    conn = get_db()
    v = conn.execute("SELECT * FROM student_verifications WHERE verify_code=?", (code,)).fetchone()
    conn.close()
    if not v:
        return jsonify({'error': 'Invalid code. Please contact hostel administration.'}), 404
    if v['is_registered']:
        return jsonify({'error': 'This code was already used. Please login or contact admin.'}), 409
    return jsonify({'id': v['id'], 'name': v['name'], 'email': v['email'] or '',
                    'course': v['course'] or '', 'year': v['year'], 'gender': v['gender'],
                    'student_type': v['student_type'], 'verify_code': v['verify_code']})

@app.route('/api/self-register', methods=['POST'])
def api_self_register():
    d = request.json
    for f in ['verify_code','username','password','name','email']:
        if not d.get(f):
            return jsonify({'error': f'{f} is required'}), 400
    conn = get_db()
    v = conn.execute("SELECT * FROM student_verifications WHERE verify_code=?", (d['verify_code'],)).fetchone()
    if not v:
        conn.close(); return jsonify({'error': 'Invalid verification code'}), 400
    if v['is_registered']:
        conn.close(); return jsonify({'error': 'Code already used. Please login.'}), 409
    if conn.execute("SELECT id FROM users WHERE username=?", (d['username'],)).fetchone():
        conn.close(); return jsonify({'error': 'Username already taken. Choose another.'}), 409
    count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    sid   = d['verify_code'] if v['student_type'] == 'existing' else f"STU{str(count+1).zfill(4)}"
    try:
        conn.execute('''INSERT INTO students
            (student_id,name,email,phone,gender,dob,address,guardian_name,guardian_phone,course,year)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (sid, d['name'], d['email'], d.get('phone'), d.get('gender', v['gender'] or 'Male'),
             d.get('dob'), d.get('address'), d.get('guardian_name'), d.get('guardian_phone'),
             d.get('course', v['course']), d.get('year', v['year'])))
        new_id = conn.execute("SELECT id FROM students WHERE student_id=?", (sid,)).fetchone()['id']
        conn.execute("INSERT INTO users (username,password,role,student_id,name) VALUES (?,?,?,?,?)",
            (d['username'], hash_pw(d['password']), 'student', new_id, d['name']))
        conn.execute("UPDATE student_verifications SET is_registered=1,registered_at=CURRENT_TIMESTAMP WHERE verify_code=?",
            (d['verify_code'],))
        conn.commit(); conn.close()
        return jsonify({'message': 'Registration successful! You can now login.'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Email or Student ID already exists. Contact admin.'}), 409

# ─── AUTH ────────────────────────────────────────────────────────────────────

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error':'Login required'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error':'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username=? AND password=?",
        (d.get('username',''), hash_pw(d.get('password','')))).fetchone()
    conn.close()
    if not u:
        return jsonify({'error':'Invalid username or password'}), 401
    session['user_id']   = u['id']
    session['username']  = u['username']
    session['role']      = u['role']
    session['name']      = u['name']
    session['student_id']= u['student_id']
    return jsonify({'role': u['role'], 'name': u['name'], 'student_id': u['student_id']})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message':'Logged out'})

@app.route('/api/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({'error':'not logged in'}), 401
    return jsonify({'username':session['username'],'role':session['role'],'name':session['name'],'student_id':session.get('student_id')})

# ─── HTML FRONTEND ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return Response(LOGIN_HTML, mimetype='text/html')
    if session.get('role') == 'admin':
        return Response(HTML, mimetype='text/html')
    return Response(STUDENT_HTML, mimetype='text/html')

@app.route('/login')
def login_page():
    session.clear()
    return Response(LOGIN_HTML, mimetype='text/html')

@app.route('/register')
def register_page():
    return Response(REGISTER_HTML, mimetype='text/html')

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hostel Management System</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<style>
:root{--sidebar-w:260px;--primary:#4f46e5;--primary-dark:#3730a3;--sidebar-bg:#1e1b4b;--sidebar-text:#c7d2fe;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#f1f5f9;color:#1e293b;}
/* Sidebar */
#sidebar{position:fixed;top:0;left:0;height:100vh;width:var(--sidebar-w);background:var(--sidebar-bg);overflow-y:auto;z-index:1000;transition:.3s;}
#sidebar .brand{padding:20px 20px 14px;border-bottom:1px solid rgba(255,255,255,.08);}
#sidebar .brand h5{color:#fff;font-weight:700;font-size:1.05rem;letter-spacing:-.01em;}
#sidebar .brand small{color:var(--sidebar-text);font-size:.72rem;}
#sidebar .nav-section{padding:16px 20px 4px;font-size:.66rem;text-transform:uppercase;letter-spacing:.1em;color:#4b5563;font-weight:600;}
#sidebar .nav-link{display:flex;align-items:center;gap:10px;padding:9px 20px;color:var(--sidebar-text);border-radius:0;font-size:.86rem;transition:.2s;cursor:pointer;text-decoration:none;}
#sidebar .nav-link:hover{background:rgba(99,102,241,.18);color:#e0e7ff;}
#sidebar .nav-link.active{background:rgba(99,102,241,.3);color:#fff;border-right:3px solid #818cf8;}
#sidebar .nav-link i{font-size:1rem;width:18px;text-align:center;}
#sidebar .nav-link .badge{margin-left:auto;}
/* Main */
#main{margin-left:var(--sidebar-w);min-height:100vh;display:flex;flex-direction:column;}
.topbar{background:#fff;padding:12px 24px;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:100;box-shadow:0 1px 3px rgba(0,0,0,.04);}
.topbar h6{font-weight:700;margin:0;flex:1;font-size:.95rem;color:#0f172a;}
.content{padding:24px;flex:1;}
/* Stat Cards */
.stat-card{background:#fff;border-radius:14px;padding:18px 20px;display:flex;align-items:center;gap:14px;box-shadow:0 1px 4px rgba(0,0,0,.07);transition:transform .15s,box-shadow .15s;}
.stat-card:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.1);}
.stat-icon{width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0;}
.stat-card h3{font-size:1.55rem;font-weight:800;margin:0;letter-spacing:-.02em;}
.stat-card p{color:#64748b;font-size:.78rem;margin:0;font-weight:500;}
.stat-card .trend{font-size:.72rem;margin-top:2px;}
/* Info Panel */
.info-panel{background:#fff;border-radius:14px;box-shadow:0 1px 4px rgba(0,0,0,.07);overflow:hidden;}
.info-panel .panel-header{padding:14px 18px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;}
.info-panel .panel-header h6{font-weight:700;font-size:.88rem;margin:0;color:#0f172a;}
/* Occupancy Bar */
.occ-bar-wrap{padding:14px 18px;display:flex;flex-direction:column;gap:10px;}
.occ-item{display:flex;flex-direction:column;gap:4px;}
.occ-label{display:flex;justify-content:space-between;font-size:.78rem;font-weight:600;color:#374151;}
.occ-track{height:8px;background:#e2e8f0;border-radius:99px;overflow:hidden;}
.occ-fill{height:100%;border-radius:99px;transition:width .6s ease;}
/* Fee Summary Widget */
.fee-stat{display:flex;align-items:center;justify-content:space-between;padding:12px 18px;border-bottom:1px solid #f1f5f9;}
.fee-stat:last-child{border-bottom:none;}
.fee-stat-label{font-size:.8rem;font-weight:600;color:#64748b;}
.fee-stat-val{font-size:1rem;font-weight:800;}
/* Quick Action Bar */
.quick-actions{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;}
.qa-btn{display:flex;align-items:center;gap:8px;padding:9px 16px;border-radius:10px;font-size:.83rem;font-weight:600;border:none;cursor:pointer;transition:.2s;}
.qa-btn:hover{filter:brightness(.93);transform:translateY(-1px);}
/* General Card */
.card{border:none;border-radius:14px;box-shadow:0 1px 4px rgba(0,0,0,.07);}
.card-header{background:#fff;border-bottom:1px solid #f1f5f9;border-radius:14px 14px 0 0!important;padding:13px 18px;font-weight:700;font-size:.88rem;color:#0f172a;}
/* Page */
.page{display:none;}.page.active{display:block;}
/* Table */
.table-responsive{border-radius:8px;overflow:hidden;}
table th{font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b;background:#f8fafc;font-weight:700;padding:10px 14px;}
table td{vertical-align:middle;font-size:.86rem;padding:10px 14px;}
table tbody tr:hover{background:#f8fafc;}
/* Badge */
.badge-available{background:#dcfce7;color:#166534;}
.badge-full{background:#fee2e2;color:#991b1b;}
.badge-maintenance{background:#fef9c3;color:#854d0e;}
.badge-active{background:#dbeafe;color:#1e40af;}
.badge-paid{background:#dcfce7;color:#166534;}
.badge-pending{background:#fff7ed;color:#c2410c;}
.badge-open{background:#fee2e2;color:#991b1b;}
.badge-resolved{background:#dcfce7;color:#166534;}
.badge-inprogress{background:#fef9c3;color:#854d0e;}
/* Avatar */
.avatar{width:36px;height:36px;border-radius:50%;background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.78rem;flex-shrink:0;}
/* Toast */
#toast-wrap{position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;}
.toast-msg{background:#1e293b;color:#fff;padding:12px 18px;border-radius:10px;font-size:.875rem;min-width:260px;display:flex;align-items:center;gap:10px;animation:fadeIn .25s;}
.toast-msg.success{border-left:4px solid #22c55e;}
.toast-msg.error{border-left:4px solid #ef4444;}
.toast-msg.info{border-left:4px solid #3b82f6;}
@keyframes fadeIn{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:translateX(0)}}
/* Form */
.form-label{font-size:.82rem;font-weight:600;color:#374151;}
.form-control,.form-select{font-size:.875rem;border-radius:8px;border:1px solid #e2e8f0;}
.form-control:focus,.form-select:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(79,70,229,.1);}
.btn-primary{background:var(--primary);border-color:var(--primary);}
.btn-primary:hover{background:var(--primary-dark);border-color:var(--primary-dark);}
/* Search bar */
.search-bar{position:relative;}.search-bar i{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#94a3b8;}
.search-bar input{padding-left:34px;}
/* Print */
@media print{#sidebar,#main .topbar,.no-print{display:none!important;}#main{margin:0;}}
.receipt-box{font-family:monospace;border:2px dashed #ccc;padding:20px;max-width:400px;margin:0 auto;}
/* Responsive */
@media(max-width:768px){#sidebar{width:0;overflow:hidden;}#main{margin-left:0;}}
</style>
</head>
<body>

<!-- SIDEBAR -->
<nav id="sidebar">
  <div class="brand">
    <h5><i class="bi bi-building-fill text-indigo-400"></i> HostelMS</h5>
    <small>Management System</small>
  </div>
  <div class="mt-2">
    <div class="nav-section">Main</div>
    <a class="nav-link active" onclick="showPage('dashboard')"><i class="bi bi-grid-1x2-fill"></i> Dashboard</a>
    <a class="nav-link" onclick="showPage('rooms')"><i class="bi bi-building"></i> Rooms</a>
    <a class="nav-link" onclick="showPage('students')"><i class="bi bi-people-fill"></i> Students</a>
    <a class="nav-section mt-2">Operations</a>
    <a class="nav-link" onclick="showPage('allocations')"><i class="bi bi-key-fill"></i> Allocations</a>
    <a class="nav-link" onclick="showPage('fees')"><i class="bi bi-cash-coin"></i> Fee Management</a>
    <a class="nav-section mt-2">Hostel</a>
    <a class="nav-link" onclick="showPage('complaints')"><i class="bi bi-chat-square-dots-fill"></i> Complaints <span class="badge bg-danger" id="badge-complaints"></span></a>
    <a class="nav-link" onclick="showPage('notices')"><i class="bi bi-megaphone-fill"></i> Notice Board</a>
    <a class="nav-link" onclick="showPage('visitors')"><i class="bi bi-person-badge-fill"></i> Visitors</a>
    <div class="nav-section mt-2">Admin</div>
    <a class="nav-link" onclick="showPage('verifications')"><i class="bi bi-shield-check-fill"></i> Student Verifications</a>
  </div>
</nav>

<!-- MAIN -->
<div id="main">
  <div class="topbar">
    <button class="btn btn-sm btn-light d-md-none" onclick="toggleSidebar()"><i class="bi bi-list fs-5"></i></button>
    <h6 id="topbar-title">Dashboard</h6>
    <div class="ms-auto d-flex gap-2 align-items-center">
      <span class="text-muted small" id="topbar-date"></span>
      <span class="text-muted small fw-semibold" id="admin-name"></span>
      <div class="avatar">AD</div>
      <button class="btn btn-sm btn-outline-secondary" onclick="doLogout()"><i class="bi bi-box-arrow-right"></i></button>
    </div>
  </div>

  <div class="content">

  <!-- ═══════════════ DASHBOARD ═══════════════ -->
  <div class="page active" id="page-dashboard">

    <!-- Quick Actions -->
    <div class="quick-actions">
      <button class="qa-btn" style="background:#ede9fe;color:#4f46e5" onclick="showPage('students')"><i class="bi bi-person-plus-fill"></i>Add Student</button>
      <button class="qa-btn" style="background:#dcfce7;color:#16a34a" onclick="showPage('allocations')"><i class="bi bi-key-fill"></i>Allocate Room</button>
      <button class="qa-btn" style="background:#fff7ed;color:#ea580c" onclick="showPage('fees')"><i class="bi bi-receipt"></i>Record Fee</button>
      <button class="qa-btn" style="background:#fef9c3;color:#854d0e" onclick="showPage('notices')"><i class="bi bi-megaphone-fill"></i>Post Notice</button>
      <button class="qa-btn" style="background:#fee2e2;color:#991b1b" onclick="showPage('complaints')"><i class="bi bi-chat-square-dots-fill"></i>View Complaints</button>
    </div>

    <!-- KPI Row -->
    <div class="row g-3 mb-4">
      <div class="col-6 col-sm-4 col-xl-2">
        <div class="stat-card">
          <div class="stat-icon" style="background:#ede9fe"><i class="bi bi-building" style="color:#7c3aed"></i></div>
          <div><h3 id="s-rooms">0</h3><p>Total Rooms</p></div>
        </div>
      </div>
      <div class="col-6 col-sm-4 col-xl-2">
        <div class="stat-card">
          <div class="stat-icon" style="background:#dcfce7"><i class="bi bi-people-fill" style="color:#16a34a"></i></div>
          <div><h3 id="s-students">0</h3><p>Students</p></div>
        </div>
      </div>
      <div class="col-6 col-sm-4 col-xl-2">
        <div class="stat-card">
          <div class="stat-icon" style="background:#dbeafe"><i class="bi bi-door-open-fill" style="color:#1d4ed8"></i></div>
          <div><h3 id="s-avail">0</h3><p>Available Rooms</p></div>
        </div>
      </div>
      <div class="col-6 col-sm-4 col-xl-2">
        <div class="stat-card">
          <div class="stat-icon" style="background:#dcfce7"><i class="bi bi-cash-stack" style="color:#15803d"></i></div>
          <div><h3 id="s-collected">₹0</h3><p>Fees Collected</p></div>
        </div>
      </div>
      <div class="col-6 col-sm-4 col-xl-2">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fff7ed"><i class="bi bi-exclamation-circle-fill" style="color:#ea580c"></i></div>
          <div><h3 id="s-pending">₹0</h3><p>Pending Fees</p></div>
        </div>
      </div>
      <div class="col-6 col-sm-4 col-xl-2">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fee2e2"><i class="bi bi-chat-square-dots-fill" style="color:#dc2626"></i></div>
          <div><h3 id="s-complaints">0</h3><p>Open Complaints</p></div>
        </div>
      </div>
    </div>

    <!-- Middle Row: Occupancy + Fee Summary + Recent Students -->
    <div class="row g-3 mb-4">

      <!-- Block Occupancy -->
      <div class="col-md-4">
        <div class="info-panel h-100">
          <div class="panel-header">
            <h6><i class="bi bi-bar-chart-steps me-2 text-primary"></i>Block Occupancy</h6>
            <span class="text-muted" style="font-size:.75rem" id="occ-summary"></span>
          </div>
          <div class="occ-bar-wrap" id="occ-bars">
            <div class="text-center text-muted py-3" style="font-size:.82rem">Loading...</div>
          </div>
        </div>
      </div>

      <!-- Fee Summary -->
      <div class="col-md-3">
        <div class="info-panel h-100">
          <div class="panel-header"><h6><i class="bi bi-wallet2 me-2 text-success"></i>Fee Summary</h6></div>
          <div class="fee-stat">
            <span class="fee-stat-label">Total Billed</span>
            <span class="fee-stat-val text-primary" id="fs-total">₹0</span>
          </div>
          <div class="fee-stat">
            <span class="fee-stat-label">Collected</span>
            <span class="fee-stat-val text-success" id="fs-paid">₹0</span>
          </div>
          <div class="fee-stat">
            <span class="fee-stat-label">Pending</span>
            <span class="fee-stat-val text-danger" id="fs-pending">₹0</span>
          </div>
          <div class="fee-stat">
            <span class="fee-stat-label">Collection Rate</span>
            <span class="fee-stat-val text-info" id="fs-rate">0%</span>
          </div>
          <div class="px-4 pb-3 pt-1">
            <div class="occ-track">
              <div class="occ-fill" id="fs-bar" style="background:#22c55e;width:0%"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Admissions -->
      <div class="col-md-5">
        <div class="info-panel h-100">
          <div class="panel-header">
            <h6><i class="bi bi-person-plus-fill me-2 text-primary"></i>Recent Admissions</h6>
            <button class="btn btn-sm btn-outline-primary" style="font-size:.75rem;padding:3px 10px" onclick="showPage('students')">View All</button>
          </div>
          <table class="table table-hover mb-0">
            <thead><tr><th>Student</th><th>Course</th><th>Yr</th></tr></thead>
            <tbody id="dash-students"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Bottom Row: Available Rooms -->
    <div class="info-panel">
      <div class="panel-header">
        <h6><i class="bi bi-door-open-fill me-2 text-success"></i>Available Rooms</h6>
        <button class="btn btn-sm btn-outline-success" style="font-size:.75rem;padding:3px 10px" onclick="showPage('rooms')">View All Rooms</button>
      </div>
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead><tr><th>Room No</th><th>Block</th><th>Floor</th><th>Type</th><th>Beds Free</th><th>Monthly Rent</th><th></th></tr></thead>
          <tbody id="dash-rooms"></tbody>
        </table>
      </div>
    </div>

  </div>

  <!-- ═══════════════ ROOMS ═══════════════ -->
  <div class="page" id="page-rooms">
    <div class="d-flex gap-2 mb-3 flex-wrap">
      <div class="search-bar flex-grow-1"><i class="bi bi-search"></i><input class="form-control" id="room-search" placeholder="Search rooms..." oninput="loadRooms()"></div>
      <select class="form-select" style="width:130px" id="room-filter-status" onchange="loadRooms()">
        <option value="">All Status</option><option>Available</option><option>Full</option><option>Maintenance</option>
      </select>
      <select class="form-select" style="width:110px" id="room-filter-block" onchange="loadRooms()">
        <option value="">All Blocks</option><option>A</option><option>B</option><option>C</option><option>D</option>
      </select>
      <button class="btn btn-primary" onclick="openRoomModal()"><i class="bi bi-plus-lg me-1"></i>Add Room</button>
    </div>
    <div class="card">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead><tr><th>Room No</th><th>Block</th><th>Floor</th><th>Type</th><th>Capacity</th><th>Occupied</th><th>Status</th><th>Rent (₹)</th><th>Amenities</th><th>Actions</th></tr></thead>
            <tbody id="rooms-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════ STUDENTS ═══════════════ -->
  <div class="page" id="page-students">
    <div class="d-flex gap-2 mb-3 flex-wrap">
      <div class="search-bar flex-grow-1"><i class="bi bi-search"></i><input class="form-control" id="student-search" placeholder="Search by name, ID, email, phone..." oninput="loadStudents()"></div>
      <select class="form-select" style="width:130px" id="student-filter-status" onchange="loadStudents()">
        <option value="">All</option><option value="Active">Active</option><option value="Inactive">Inactive</option>
      </select>
      <button class="btn btn-primary" onclick="openStudentModal()"><i class="bi bi-person-plus me-1"></i>Add Student</button>
    </div>
    <div class="card">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead><tr><th>ID</th><th>Name</th><th>Contact</th><th>Gender</th><th>Course</th><th>Yr</th><th>Room</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody id="students-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════ ALLOCATIONS ═══════════════ -->
  <div class="page" id="page-allocations">
    <div class="row g-3 mb-3">
      <div class="col-md-5">
        <div class="card">
          <div class="card-header"><i class="bi bi-key-fill me-2 text-primary"></i>Allocate Room</div>
          <div class="card-body">
            <div class="mb-3"><label class="form-label">Student *</label>
              <select class="form-select" id="alloc-student"><option value="">Select student...</option></select>
            </div>
            <div class="mb-3"><label class="form-label">Room *</label>
              <select class="form-select" id="alloc-room"><option value="">Select room...</option></select>
            </div>
            <div class="mb-3"><label class="form-label">Expected Vacate Date</label>
              <input type="date" class="form-control" id="alloc-expected">
            </div>
            <button class="btn btn-primary w-100" onclick="doAllocate()"><i class="bi bi-check-lg me-1"></i>Allocate Room</button>
          </div>
        </div>
      </div>
      <div class="col-md-7">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span><i class="bi bi-list-check me-2"></i>Active Allocations</span>
            <select class="form-select form-select-sm" style="width:140px" id="alloc-filter" onchange="loadAllocations()">
              <option value="Active">Active</option><option value="Vacated">Vacated</option>
            </select>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0">
                <thead><tr><th>Student</th><th>Room</th><th>From</th><th>Exp. Vacate</th><th>Action</th></tr></thead>
                <tbody id="alloc-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════ FEES ═══════════════ -->
  <div class="page" id="page-fees">
    <div class="row g-3 mb-3">
      <div class="col-md-4">
        <div class="card">
          <div class="card-header"><i class="bi bi-plus-circle-fill me-2 text-success"></i>Record Payment</div>
          <div class="card-body">
            <div class="mb-2"><label class="form-label">Student *</label>
              <select class="form-select" id="fee-student" onchange="loadFeeSummary()"><option value="">Select...</option></select>
            </div>
            <div class="mb-2"><label class="form-label">Month *</label>
              <input type="text" class="form-control" id="fee-month" placeholder="e.g. February 2026">
            </div>
            <div class="mb-2"><label class="form-label">Amount (₹) *</label>
              <input type="number" class="form-control" id="fee-amount" min="0">
            </div>
            <div class="row g-2 mb-2">
              <div class="col"><label class="form-label">Discount</label><input type="number" class="form-control" id="fee-discount" min="0" value="0"></div>
              <div class="col"><label class="form-label">Fine</label><input type="number" class="form-control" id="fee-fine" min="0" value="0"></div>
            </div>
            <div class="mb-3"><label class="form-label">Mode *</label>
              <select class="form-select" id="fee-mode">
                <option>Cash</option><option>UPI</option><option>Bank Transfer</option><option>Cheque</option><option>Card</option>
              </select>
            </div>
            <button class="btn btn-success w-100" onclick="recordPayment()"><i class="bi bi-receipt me-1"></i>Record & Print Receipt</button>
          </div>
        </div>
        <div class="card mt-3">
          <div class="card-header"><i class="bi bi-lightning-fill me-2 text-warning"></i>Generate Monthly Fees</div>
          <div class="card-body">
            <div class="mb-2"><label class="form-label">Month</label><input type="text" class="form-control" id="gen-month" placeholder="February 2026"></div>
            <div class="mb-3"><label class="form-label">Due Date</label><input type="date" class="form-control" id="gen-due"></div>
            <button class="btn btn-warning w-100 text-dark" onclick="generateFees()"><i class="bi bi-magic me-1"></i>Generate for All Students</button>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="d-flex gap-2 mb-2 flex-wrap">
          <div class="search-bar flex-grow-1"><i class="bi bi-search"></i><input class="form-control" id="fee-search" placeholder="Search fees..." oninput="loadFees()"></div>
          <select class="form-select" style="width:130px" id="fee-filter" onchange="loadFees()">
            <option value="">All</option><option value="Pending">Pending</option><option value="Paid">Paid</option>
          </select>
        </div>
        <div class="card">
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0">
                <thead><tr><th>Receipt</th><th>Student</th><th>Month</th><th>Amount</th><th>Due</th><th>Status</th><th>Mode</th><th></th></tr></thead>
                <tbody id="fees-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════ COMPLAINTS ═══════════════ -->
  <div class="page" id="page-complaints">
    <div class="row g-3">
      <div class="col-md-4">
        <div class="card">
          <div class="card-header"><i class="bi bi-plus-circle-fill me-2 text-danger"></i>New Complaint</div>
          <div class="card-body">
            <div class="mb-2"><label class="form-label">Student *</label>
              <select class="form-select" id="comp-student"><option value="">Select...</option></select>
            </div>
            <div class="mb-2"><label class="form-label">Category *</label>
              <select class="form-select" id="comp-category">
                <option>Plumbing</option><option>Electricity</option><option>Cleanliness</option>
                <option>Internet</option><option>Furniture</option><option>Food</option><option>Security</option><option>Other</option>
              </select>
            </div>
            <div class="mb-2"><label class="form-label">Priority</label>
              <select class="form-select" id="comp-priority"><option>Low</option><option selected>Medium</option><option>High</option></select>
            </div>
            <div class="mb-2"><label class="form-label">Subject *</label>
              <input type="text" class="form-control" id="comp-subject" placeholder="Brief subject">
            </div>
            <div class="mb-3"><label class="form-label">Description</label>
              <textarea class="form-control" id="comp-desc" rows="3" placeholder="Details..."></textarea>
            </div>
            <button class="btn btn-danger w-100" onclick="submitComplaint()"><i class="bi bi-send-fill me-1"></i>Submit Complaint</button>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="d-flex gap-2 mb-2">
          <select class="form-select" style="width:140px" id="comp-filter" onchange="loadComplaints()">
            <option value="">All</option><option value="Open">Open</option><option value="In Progress">In Progress</option><option value="Resolved">Resolved</option>
          </select>
        </div>
        <div class="card">
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0">
                <thead><tr><th>Student</th><th>Category</th><th>Subject</th><th>Priority</th><th>Status</th><th>Date</th><th>Actions</th></tr></thead>
                <tbody id="comp-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════ NOTICES ═══════════════ -->
  <div class="page" id="page-notices">
    <div class="row g-3">
      <div class="col-md-4">
        <div class="card">
          <div class="card-header"><i class="bi bi-megaphone-fill me-2 text-warning"></i>Post Notice</div>
          <div class="card-body">
            <div class="mb-2"><label class="form-label">Title *</label><input type="text" class="form-control" id="notice-title"></div>
            <div class="mb-2"><label class="form-label">Category</label>
              <select class="form-select" id="notice-cat">
                <option>General</option><option>Fee</option><option>Maintenance</option><option>Event</option><option>Holiday</option><option>Emergency</option>
              </select>
            </div>
            <div class="mb-2"><label class="form-label">Priority</label>
              <select class="form-select" id="notice-priority"><option>Normal</option><option>High</option><option>Urgent</option></select>
            </div>
            <div class="mb-2"><label class="form-label">Expires On</label><input type="date" class="form-control" id="notice-expires"></div>
            <div class="mb-3"><label class="form-label">Content *</label><textarea class="form-control" id="notice-content" rows="4"></textarea></div>
            <button class="btn btn-warning w-100 text-dark" onclick="postNotice()"><i class="bi bi-send me-1"></i>Post Notice</button>
          </div>
        </div>
      </div>
      <div class="col-md-8" id="notices-grid"></div>
    </div>
  </div>

  <!-- ═══════════════ VISITORS ═══════════════ -->
  <div class="page" id="page-visitors">
    <div class="row g-3">
      <div class="col-md-4">
        <div class="card">
          <div class="card-header"><i class="bi bi-person-plus-fill me-2 text-primary"></i>Check In Visitor</div>
          <div class="card-body">
            <div class="mb-2"><label class="form-label">Student Being Visited *</label>
              <select class="form-select" id="vis-student"><option value="">Select...</option></select>
            </div>
            <div class="mb-2"><label class="form-label">Visitor Name *</label><input type="text" class="form-control" id="vis-name"></div>
            <div class="mb-2"><label class="form-label">Relation</label><input type="text" class="form-control" id="vis-relation" placeholder="Parent/Friend/Sibling"></div>
            <div class="mb-2"><label class="form-label">Phone</label><input type="text" class="form-control" id="vis-phone"></div>
            <div class="mb-3"><label class="form-label">Purpose</label><input type="text" class="form-control" id="vis-purpose"></div>
            <button class="btn btn-primary w-100" onclick="checkInVisitor()"><i class="bi bi-box-arrow-in-right me-1"></i>Check In</button>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="card">
          <div class="card-header"><i class="bi bi-clock-history me-2"></i>Visitor Log (Recent 50)</div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0">
                <thead><tr><th>Visitor</th><th>Student</th><th>Relation</th><th>Purpose</th><th>Check In</th><th>Check Out</th><th></th></tr></thead>
                <tbody id="vis-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════ STUDENT VERIFICATIONS ═══════════════ -->
  <div class="page" id="page-verifications">
    <div class="row g-3">
      <div class="col-md-4">
        <div class="card">
          <div class="card-header"><i class="bi bi-shield-plus-fill me-2 text-success"></i>Add Verification Code</div>
          <div class="card-body">
            <div class="mb-2"><label class="form-label">Verification Code / Admission No *</label>
              <input class="form-control" id="vf-code" placeholder="e.g. ADM2026005 or S005"></div>
            <div class="mb-2"><label class="form-label">Student Type</label>
              <select class="form-select" id="vf-type">
                <option value="fresher">Fresher (Admission No)</option>
                <option value="existing">Existing Student (Roll No)</option>
              </select></div>
            <div class="mb-2"><label class="form-label">Full Name *</label>
              <input class="form-control" id="vf-name" placeholder="Student's full name"></div>
            <div class="mb-2"><label class="form-label">Email</label>
              <input type="email" class="form-control" id="vf-email"></div>
            <div class="mb-2"><label class="form-label">Course</label>
              <input class="form-control" id="vf-course" placeholder="B.Tech CSE"></div>
            <div class="row g-2 mb-3">
              <div class="col"><label class="form-label">Year</label>
                <select class="form-select" id="vf-year"><option value="1">1st</option><option value="2">2nd</option><option value="3">3rd</option><option value="4">4th</option></select></div>
              <div class="col"><label class="form-label">Gender</label>
                <select class="form-select" id="vf-gender"><option>Male</option><option>Female</option><option>Other</option></select></div>
            </div>
            <button class="btn btn-success w-100" onclick="addVerification()"><i class="bi bi-plus-lg me-1"></i>Add Verification Record</button>
            <hr class="my-3">
            <div class="alert alert-info p-2" style="font-size:.8rem">
              <i class="bi bi-info-circle me-1"></i><strong>How it works:</strong> Add a record here with the student's admission/counselling number. The student uses that code at <code>/register</code> to self-register.
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="d-flex gap-2 mb-2">
          <span class="fw-semibold">Pre-Approved Student List</span>
          <button class="btn btn-sm btn-outline-primary ms-auto" onclick="loadVerifications()"><i class="bi bi-arrow-clockwise"></i> Refresh</button>
          <a href="/register" target="_blank" class="btn btn-sm btn-outline-success"><i class="bi bi-box-arrow-up-right me-1"></i>Open Register Page</a>
        </div>
        <div class="card"><div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead><tr><th>Code</th><th>Type</th><th>Name</th><th>Course</th><th>Email</th><th>Status</th><th>Registered</th><th></th></tr></thead>
              <tbody id="verif-tbody"></tbody>
            </table>
          </div>
        </div></div>
      </div>
    </div>
  </div>

  </div><!-- /content -->
</div><!-- /main -->

<!-- TOAST WRAPPER -->
<div id="toast-wrap"></div>

<!-- MODAL: Room -->
<div class="modal fade" id="roomModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header"><h5 class="modal-title" id="roomModalTitle">Add Room</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
      <div class="modal-body">
        <input type="hidden" id="rm-id">
        <div class="row g-2">
          <div class="col-6"><label class="form-label">Room No *</label><input class="form-control" id="rm-no"></div>
          <div class="col-6"><label class="form-label">Block *</label><input class="form-control" id="rm-block" placeholder="A / B / C"></div>
          <div class="col-6"><label class="form-label">Floor *</label><input type="number" class="form-control" id="rm-floor" min="1" value="1"></div>
          <div class="col-6"><label class="form-label">Type</label>
            <select class="form-select" id="rm-type"><option>Single</option><option>Double</option><option>Triple</option><option>Dormitory</option></select>
          </div>
          <div class="col-6"><label class="form-label">Capacity *</label><input type="number" class="form-control" id="rm-capacity" min="1" value="1"></div>
          <div class="col-6"><label class="form-label">Monthly Rent (₹) *</label><input type="number" class="form-control" id="rm-rent" min="0"></div>
          <div class="col-6"><label class="form-label">Deposit (₹)</label><input type="number" class="form-control" id="rm-deposit" min="0" value="0"></div>
          <div class="col-6"><label class="form-label">Status</label>
            <select class="form-select" id="rm-status"><option>Available</option><option>Maintenance</option></select>
          </div>
          <div class="col-12"><label class="form-label">Amenities</label><input class="form-control" id="rm-amenities" placeholder="AC, Wi-Fi, Geyser..."></div>
          <div class="col-12"><label class="form-label">Description</label><textarea class="form-control" id="rm-desc" rows="2"></textarea></div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button class="btn btn-primary" onclick="saveRoom()">Save Room</button>
      </div>
    </div>
  </div>
</div>

<!-- MODAL: Student -->
<div class="modal fade" id="studentModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header"><h5 class="modal-title" id="studentModalTitle">Add Student</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
      <div class="modal-body">
        <input type="hidden" id="stu-id">
        <div class="row g-2">
          <div class="col-md-4"><label class="form-label">Student ID *</label><input class="form-control" id="stu-sid"></div>
          <div class="col-md-4"><label class="form-label">Full Name *</label><input class="form-control" id="stu-name"></div>
          <div class="col-md-4"><label class="form-label">Email *</label><input type="email" class="form-control" id="stu-email"></div>
          <div class="col-md-4"><label class="form-label">Phone</label><input class="form-control" id="stu-phone"></div>
          <div class="col-md-4"><label class="form-label">Gender</label>
            <select class="form-select" id="stu-gender"><option>Male</option><option>Female</option><option>Other</option></select>
          </div>
          <div class="col-md-4"><label class="form-label">Date of Birth</label><input type="date" class="form-control" id="stu-dob"></div>
          <div class="col-md-6"><label class="form-label">Course</label><input class="form-control" id="stu-course" placeholder="B.Tech CSE"></div>
          <div class="col-md-6"><label class="form-label">Year</label><input type="number" class="form-control" id="stu-year" min="1" max="6"></div>
          <div class="col-12"><label class="form-label">Address</label><textarea class="form-control" id="stu-address" rows="2"></textarea></div>
          <div class="col-md-6"><label class="form-label">Guardian Name</label><input class="form-control" id="stu-gname"></div>
          <div class="col-md-6"><label class="form-label">Guardian Phone</label><input class="form-control" id="stu-gphone"></div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button class="btn btn-primary" onclick="saveStudent()">Save Student</button>
      </div>
    </div>
  </div>
</div>

<!-- MODAL: Vacate -->
<div class="modal fade" id="vacateModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header"><h5 class="modal-title">Vacate Room</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
      <div class="modal-body">
        <input type="hidden" id="vacate-id">
        <p id="vacate-info" class="mb-3"></p>
        <label class="form-label">Remarks</label>
        <textarea class="form-control" id="vacate-remarks" rows="3" placeholder="Reason for vacating..."></textarea>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button class="btn btn-danger" onclick="doVacate()">Confirm Vacate</button>
      </div>
    </div>
  </div>
</div>

<!-- MODAL: Complaint Status -->
<div class="modal fade" id="compModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header"><h5 class="modal-title">Update Complaint</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
      <div class="modal-body">
        <input type="hidden" id="comp-update-id">
        <div class="mb-2"><label class="form-label">Status</label>
          <select class="form-select" id="comp-update-status"><option>Open</option><option>In Progress</option><option>Resolved</option></select>
        </div>
        <div class="mb-0"><label class="form-label">Remarks</label>
          <textarea class="form-control" id="comp-update-remark" rows="3"></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button class="btn btn-primary" onclick="updateComplaint()">Update</button>
      </div>
    </div>
  </div>
</div>

<!-- MODAL: Receipt Print -->
<div class="modal fade" id="receiptModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header"><h5 class="modal-title">Fee Receipt</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" id="receipt-content"></div>
      <div class="modal-footer no-print">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        <button class="btn btn-primary" onclick="window.print()"><i class="bi bi-printer me-1"></i>Print</button>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
// ── Globals ──────────────────────────────────────────────────────────────────
let charts = {};

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('topbar-date').textContent = new Date().toLocaleDateString('en-IN',{weekday:'short',day:'numeric',month:'short',year:'numeric'});
  fetch('/api/me').then(r=>r.json()).then(d=>{ if(d.name) document.getElementById('admin-name').textContent=d.name; }).catch(()=>{});
  loadDashboard();
  loadStudentDropdowns();
  // Set default month/due for fees
  const now = new Date();
  document.getElementById('fee-month').value = now.toLocaleString('default',{month:'long'})+' '+now.getFullYear();
  document.getElementById('gen-month').value = now.toLocaleString('default',{month:'long'})+' '+now.getFullYear();
  const due = new Date(now.getFullYear(),now.getMonth(),10);
  document.getElementById('gen-due').value = due.toISOString().split('T')[0];
});

// ── Navigation ────────────────────────────────────────────────────────────────
function showPage(name){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  document.querySelectorAll('#sidebar .nav-link').forEach(l=>l.classList.remove('active'));
  document.querySelector(`#sidebar .nav-link[onclick*="${name}"]`)?.classList.add('active');
  const titles={dashboard:'Dashboard',rooms:'Room Management',students:'Student Management',
    allocations:'Room Allocations',fees:'Fee Management',complaints:'Complaints',
    notices:'Notice Board',visitors:'Visitor Log'};
  document.getElementById('topbar-title').textContent=titles[name]||name;
  const loaders={rooms:loadRooms,students:loadStudents,allocations:()=>{loadAllocations();loadAllocDropdowns();},
    fees:loadFees,complaints:loadComplaints,notices:loadNotices,visitors:loadVisitors,verifications:loadVerifications};
  loaders[name]?.();
}
function toggleSidebar(){
  const s=document.getElementById('sidebar');
  s.style.width=s.style.width==='260px'||!s.style.width?'0':'260px';
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg,type='success'){
  const el=document.createElement('div');
  el.className=`toast-msg ${type}`;
  const icons={success:'bi-check-circle-fill',error:'bi-x-circle-fill',info:'bi-info-circle-fill'};
  el.innerHTML=`<i class="bi ${icons[type]||'bi-info-circle-fill'}"></i>${msg}`;
  document.getElementById('toast-wrap').appendChild(el);
  setTimeout(()=>el.remove(),3500);
}

// ── API Helper ────────────────────────────────────────────────────────────────
async function api(url,method='GET',body=null){
  const opts={method,headers:{'Content-Type':'application/json'}};
  if(body) opts.body=JSON.stringify(body);
  const r=await fetch(url,opts);
  const d=await r.json();
  if(!r.ok) throw new Error(d.error||'Request failed');
  return d;
}

// ── Status Badge ─────────────────────────────────────────────────────────────
function badge(val){
  const map={'Available':'available','Full':'full','Maintenance':'maintenance',
    'Active':'active','Paid':'paid','Pending':'pending','Open':'open',
    'Resolved':'resolved','In Progress':'inprogress','Vacated':'maintenance','Inactive':'maintenance'};
  const cls=map[val]||'active';
  return `<span class="badge badge-${cls}">${val}</span>`;
}
function priorityBadge(p){
  const m={'High':'danger','Medium':'warning','Low':'success','Urgent':'danger','Normal':'secondary'};
  return `<span class="badge bg-${m[p]||'secondary'} bg-opacity-15 text-${m[p]||'secondary'}">${p}</span>`;
}

// ── DASHBOARD ─────────────────────────────────────────────────────────────────
async function loadDashboard(){
  try{
    const d=await api('/api/stats');
    // KPI cards
    document.getElementById('s-rooms').textContent=d.total_rooms;
    document.getElementById('s-students').textContent=d.total_students;
    document.getElementById('s-avail').textContent=d.available_rooms;
    document.getElementById('s-collected').textContent='₹'+d.collected_fees.toLocaleString('en-IN');
    document.getElementById('s-pending').textContent='₹'+d.pending_fees.toLocaleString('en-IN');
    document.getElementById('s-complaints').textContent=d.open_complaints;
    if(d.open_complaints>0) document.getElementById('badge-complaints').textContent=d.open_complaints;

    // Fee summary widget
    const total=d.collected_fees+d.pending_fees;
    const rate=total>0?Math.round(d.collected_fees/total*100):0;
    document.getElementById('fs-total').textContent='₹'+total.toLocaleString('en-IN');
    document.getElementById('fs-paid').textContent='₹'+d.collected_fees.toLocaleString('en-IN');
    document.getElementById('fs-pending').textContent='₹'+d.pending_fees.toLocaleString('en-IN');
    document.getElementById('fs-rate').textContent=rate+'%';
    document.getElementById('fs-bar').style.width=rate+'%';

    // Block occupancy bars
    buildOccupancyBars(d);

    // Available rooms table
    document.getElementById('dash-rooms').innerHTML=d.available_room_list.length
      ?d.available_room_list.map(r=>`
        <tr>
          <td><strong class="text-primary">${r.room_no}</strong></td>
          <td><span class="badge" style="background:#ede9fe;color:#4f46e5">Block ${r.block}</span></td>
          <td>${r.floor}</td>
          <td>${r.type}</td>
          <td><span class="fw-semibold text-success">${r.capacity-r.occupied}</span> <small class="text-muted">of ${r.capacity}</small></td>
          <td class="fw-semibold">₹${r.rent.toLocaleString('en-IN')}<small class="text-muted fw-normal">/mo</small></td>
          <td><button class="btn btn-sm btn-primary" onclick="showPage('allocations')">Allocate</button></td>
        </tr>
      `).join('')
      :'<tr><td colspan="7" class="text-center text-muted py-4"><i class="bi bi-check-circle text-success fs-4 d-block mb-1"></i>All rooms are fully occupied</td></tr>';

    // Recent students
    document.getElementById('dash-students').innerHTML=d.recent_students.map(s=>`
      <tr>
        <td><div class="d-flex align-items-center gap-2">
          <div class="avatar" style="width:30px;height:30px;font-size:.73rem">${s.name.charAt(0)}</div>
          <div><div style="font-size:.84rem;font-weight:600">${s.name}</div><div style="font-size:.73rem;color:#64748b">${s.student_id}</div></div>
        </div></td>
        <td style="font-size:.8rem">${s.course||'—'}</td>
        <td><span class="badge" style="background:#f1f5f9;color:#374151">Yr ${s.year||'—'}</span></td>
      </tr>
    `).join('');

  }catch(e){ toast('Failed to load dashboard: '+e.message,'error'); }
}

function buildOccupancyBars(d){
  // Compute per-block stats from room_type_stats (fallback: use total)
  // We'll fetch rooms data to get per-block info
  fetch('/api/rooms').then(r=>r.json()).then(rooms=>{
    const blocks={};
    rooms.forEach(r=>{
      if(!blocks[r.block]) blocks[r.block]={cap:0,occ:0};
      blocks[r.block].cap+=r.capacity;
      blocks[r.block].occ+=r.occupied;
    });
    const colors={'A':'#4f46e5','B':'#0ea5e9','C':'#10b981','D':'#f59e0b','E':'#ef4444'};
    const totalCap=Object.values(blocks).reduce((s,b)=>s+b.cap,0);
    const totalOcc=Object.values(blocks).reduce((s,b)=>s+b.occ,0);
    document.getElementById('occ-summary').textContent=`${totalOcc}/${totalCap} occupied`;
    document.getElementById('occ-bars').innerHTML=Object.entries(blocks).map(([blk,b])=>{
      const pct=b.cap>0?Math.round(b.occ/b.cap*100):0;
      const col=colors[blk]||'#6366f1';
      return `<div class="occ-item">
        <div class="occ-label"><span>Block ${blk}</span><span style="color:${col}">${b.occ}/${b.cap} &nbsp;(${pct}%)</span></div>
        <div class="occ-track"><div class="occ-fill" style="width:${pct}%;background:${col}"></div></div>
      </div>`;
    }).join('');
  }).catch(()=>{});
}

// ── ROOMS ─────────────────────────────────────────────────────────────────────
async function loadRooms(){
  const q=document.getElementById('room-search').value;
  const status=document.getElementById('room-filter-status').value;
  const block=document.getElementById('room-filter-block').value;
  try{
    const rows=await api(`/api/rooms?q=${encodeURIComponent(q)}&status=${status}&block=${block}`);
    document.getElementById('rooms-tbody').innerHTML=rows.length?rows.map(r=>`
      <tr>
        <td><strong>${r.room_no}</strong></td>
        <td>${r.block}</td><td>${r.floor}</td><td>${r.type}</td>
        <td>${r.capacity}</td><td>${r.occupied}</td>
        <td>${badge(r.status)}</td>
        <td>₹${r.rent.toLocaleString('en-IN')}</td>
        <td><small class="text-muted">${r.amenities||'-'}</small></td>
        <td>
          <button class="btn btn-sm btn-outline-warning me-1" onclick="openRoomModal(${r.id})"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteRoom(${r.id})"><i class="bi bi-wrench"></i></button>
        </td>
      </tr>
    `).join(''):'<tr><td colspan="10" class="text-center text-muted py-4">No rooms found</td></tr>';
  }catch(e){ toast('Failed to load rooms: '+e.message,'error'); }
}

async function openRoomModal(id=null){
  document.getElementById('rm-id').value='';
  document.getElementById('roomModalTitle').textContent=id?'Edit Room':'Add Room';
  ['rm-no','rm-block','rm-amenities','rm-desc'].forEach(i=>document.getElementById(i).value='');
  ['rm-floor','rm-capacity'].forEach(i=>document.getElementById(i).value=1);
  document.getElementById('rm-deposit').value=0;
  document.getElementById('rm-rent').value='';
  if(id){
    const r=await api(`/api/rooms/${id}`);
    document.getElementById('rm-id').value=id;
    document.getElementById('rm-no').value=r.room_no;
    document.getElementById('rm-block').value=r.block;
    document.getElementById('rm-floor').value=r.floor;
    document.getElementById('rm-type').value=r.type;
    document.getElementById('rm-capacity').value=r.capacity;
    document.getElementById('rm-rent').value=r.rent;
    document.getElementById('rm-deposit').value=r.deposit||0;
    document.getElementById('rm-amenities').value=r.amenities||'';
    document.getElementById('rm-desc').value=r.description||'';
    document.getElementById('rm-status').value=r.status;
  }
  new bootstrap.Modal(document.getElementById('roomModal')).show();
}

async function saveRoom(){
  const id=document.getElementById('rm-id').value;
  const data={
    room_no:document.getElementById('rm-no').value,
    block:document.getElementById('rm-block').value,
    floor:+document.getElementById('rm-floor').value,
    type:document.getElementById('rm-type').value,
    capacity:+document.getElementById('rm-capacity').value,
    rent:+document.getElementById('rm-rent').value,
    deposit:+document.getElementById('rm-deposit').value,
    amenities:document.getElementById('rm-amenities').value,
    description:document.getElementById('rm-desc').value,
    status:document.getElementById('rm-status').value
  };
  try{
    if(id){ await api(`/api/rooms/${id}`,'PUT',data); toast('Room updated'); }
    else   { await api('/api/rooms','POST',data); toast('Room added'); }
    bootstrap.Modal.getInstance(document.getElementById('roomModal')).hide();
    loadRooms();
    loadAllocDropdowns();
  }catch(e){ toast(e.message,'error'); }
}

async function deleteRoom(id){
  if(!confirm('Move room to Maintenance?')) return;
  try{ await api(`/api/rooms/${id}`,'DELETE'); toast('Room moved to Maintenance','info'); loadRooms(); }
  catch(e){ toast(e.message,'error'); }
}

// ── STUDENTS ──────────────────────────────────────────────────────────────────
async function loadStudents(){
  const q=document.getElementById('student-search').value;
  const s=document.getElementById('student-filter-status').value;
  try{
    const rows=await api(`/api/students?q=${encodeURIComponent(q)}&status=${s}`);
    // Load allocations for room display
    const allocs=await api('/api/allocations?status=Active');
    const roomMap={};
    allocs.forEach(a=>roomMap[a.student_id]=`${a.room_no}/${a.block}`);
    document.getElementById('students-tbody').innerHTML=rows.length?rows.map(r=>`
      <tr>
        <td><span class="fw-semibold text-primary">${r.student_id}</span></td>
        <td><div class="d-flex align-items-center gap-2"><div class="avatar" style="width:30px;height:30px;font-size:.75rem">${r.name.charAt(0)}</div>${r.name}</div></td>
        <td><small>${r.phone||'-'}<br><span class="text-muted">${r.email}</span></small></td>
        <td>${r.gender}</td>
        <td>${r.course||'-'}</td>
        <td>${r.year||'-'}</td>
        <td>${roomMap[r.id]?`<span class="badge badge-active">${roomMap[r.id]}</span>`:'<span class="text-muted">-</span>'}</td>
        <td>${badge(r.status)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary me-1" onclick="openStudentModal(${r.id})"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteStudent(${r.id})"><i class="bi bi-person-x"></i></button>
        </td>
      </tr>
    `).join(''):'<tr><td colspan="9" class="text-center text-muted py-4">No students found</td></tr>';
  }catch(e){ toast('Failed to load students: '+e.message,'error'); }
}

async function openStudentModal(id=null){
  document.getElementById('stu-id').value='';
  document.getElementById('studentModalTitle').textContent=id?'Edit Student':'Add Student';
  ['stu-sid','stu-name','stu-email','stu-phone','stu-course','stu-address','stu-gname','stu-gphone','stu-dob'].forEach(i=>document.getElementById(i).value='');
  document.getElementById('stu-year').value='';
  if(id){
    const s=await api(`/api/students/${id}`);
    document.getElementById('stu-id').value=id;
    document.getElementById('stu-sid').value=s.student_id;
    document.getElementById('stu-name').value=s.name;
    document.getElementById('stu-email').value=s.email;
    document.getElementById('stu-phone').value=s.phone||'';
    document.getElementById('stu-gender').value=s.gender||'Male';
    document.getElementById('stu-dob').value=s.dob||'';
    document.getElementById('stu-course').value=s.course||'';
    document.getElementById('stu-year').value=s.year||'';
    document.getElementById('stu-address').value=s.address||'';
    document.getElementById('stu-gname').value=s.guardian_name||'';
    document.getElementById('stu-gphone').value=s.guardian_phone||'';
  }
  new bootstrap.Modal(document.getElementById('studentModal')).show();
}

async function saveStudent(){
  const id=document.getElementById('stu-id').value;
  const data={
    student_id:document.getElementById('stu-sid').value,
    name:document.getElementById('stu-name').value,
    email:document.getElementById('stu-email').value,
    phone:document.getElementById('stu-phone').value,
    gender:document.getElementById('stu-gender').value,
    dob:document.getElementById('stu-dob').value,
    course:document.getElementById('stu-course').value,
    year:document.getElementById('stu-year').value||null,
    address:document.getElementById('stu-address').value,
    guardian_name:document.getElementById('stu-gname').value,
    guardian_phone:document.getElementById('stu-gphone').value,
    status:'Active'
  };
  try{
    if(id){ await api(`/api/students/${id}`,'PUT',data); toast('Student updated'); }
    else   { await api('/api/students','POST',data); toast('Student added'); }
    bootstrap.Modal.getInstance(document.getElementById('studentModal')).hide();
    loadStudents(); loadStudentDropdowns();
  }catch(e){ toast(e.message,'error'); }
}

async function deleteStudent(id){
  if(!confirm('Deactivate this student?')) return;
  try{ await api(`/api/students/${id}`,'DELETE'); toast('Student deactivated','info'); loadStudents(); }
  catch(e){ toast(e.message,'error'); }
}

// ── ALLOCATIONS ───────────────────────────────────────────────────────────────
async function loadAllocDropdowns(){
  try{
    const [students,rooms]=await Promise.all([
      api('/api/students?status=Active'),
      api('/api/rooms/available')
    ]);
    document.getElementById('alloc-student').innerHTML=
      '<option value="">Select student...</option>'+
      students.map(s=>`<option value="${s.id}">${s.name} (${s.student_id})</option>`).join('');
    document.getElementById('alloc-room').innerHTML=
      '<option value="">Select room...</option>'+
      rooms.map(r=>`<option value="${r.id}">Room ${r.room_no} · Block ${r.block} · ${r.type} · ${r.capacity-r.occupied} bed(s) · ₹${r.rent}/mo</option>`).join('');
  }catch(e){}
}

async function loadAllocations(){
  const status=document.getElementById('alloc-filter').value;
  try{
    const rows=await api(`/api/allocations?status=${status}`);
    document.getElementById('alloc-tbody').innerHTML=rows.length?rows.map(r=>`
      <tr>
        <td><div class="fw-semibold">${r.student_name}</div><small class="text-muted">${r.student_id}</small></td>
        <td>Room <strong>${r.room_no}</strong><br><small>Block ${r.block} · ${r.type}</small></td>
        <td><small>${r.allocated_date}</small></td>
        <td><small>${r.expected_vacate||'—'}</small></td>
        <td>${status==='Active'?`<button class="btn btn-sm btn-outline-danger" onclick="openVacate(${r.id},'${r.student_name}','${r.room_no}')"><i class="bi bi-box-arrow-right me-1"></i>Vacate</button>`:'<span class="badge badge-maintenance">Vacated</span>'}</td>
      </tr>
    `).join(''):'<tr><td colspan="5" class="text-center text-muted py-4">No allocations</td></tr>';
  }catch(e){ toast(e.message,'error'); }
}

async function doAllocate(){
  const student_id=document.getElementById('alloc-student').value;
  const room_id=document.getElementById('alloc-room').value;
  const expected=document.getElementById('alloc-expected').value;
  if(!student_id||!room_id){ toast('Select student and room','error'); return; }
  try{
    await api('/api/allocate','POST',{student_id,room_id,expected_vacate:expected||null});
    toast('Room allocated successfully!');
    loadAllocations(); loadAllocDropdowns(); loadDashboard();
  }catch(e){ toast(e.message,'error'); }
}

function openVacate(id,sname,rno){
  document.getElementById('vacate-id').value=id;
  document.getElementById('vacate-info').innerHTML=`Vacate <strong>${sname}</strong> from Room <strong>${rno}</strong>?`;
  document.getElementById('vacate-remarks').value='';
  new bootstrap.Modal(document.getElementById('vacateModal')).show();
}

async function doVacate(){
  const id=document.getElementById('vacate-id').value;
  const remarks=document.getElementById('vacate-remarks').value;
  try{
    await api('/api/vacate','POST',{allocation_id:id,remarks});
    bootstrap.Modal.getInstance(document.getElementById('vacateModal')).hide();
    toast('Room vacated successfully','info');
    loadAllocations(); loadAllocDropdowns(); loadDashboard();
  }catch(e){ toast(e.message,'error'); }
}

// ── FEES ──────────────────────────────────────────────────────────────────────
async function loadStudentDropdowns(){
  try{
    const students=await api('/api/students?status=Active');
    const opts='<option value="">Select...</option>'+students.map(s=>`<option value="${s.id}">${s.name} (${s.student_id})</option>`).join('');
    ['fee-student','comp-student','vis-student'].forEach(id=>{
      const el=document.getElementById(id);
      if(el) el.innerHTML=opts;
    });
  }catch(e){}
}

async function loadFees(){
  const q=document.getElementById('fee-search').value;
  const status=document.getElementById('fee-filter').value;
  try{
    const rows=await api(`/api/fees?q=${encodeURIComponent(q)}&status=${status}`);
    document.getElementById('fees-tbody').innerHTML=rows.length?rows.map(r=>`
      <tr>
        <td><small class="font-monospace">${r.receipt_no||'—'}</small></td>
        <td>${r.student_name}</td>
        <td>${r.month||'—'}</td>
        <td>₹${r.amount.toLocaleString('en-IN')}</td>
        <td><small>${r.due_date}</small></td>
        <td>${badge(r.status)}</td>
        <td><small>${r.payment_mode||'—'}</small></td>
        <td>${r.status==='Pending'?`<button class="btn btn-xs btn-sm btn-outline-success" onclick="markPaid(${r.id})"><i class="bi bi-check"></i></button>`:''}
            <button class="btn btn-sm btn-outline-secondary" onclick="printReceipt('${r.receipt_no||''}','${r.student_name}','${r.month||''}',${r.amount},'${r.paid_date||r.due_date}','${r.payment_mode||''}')"><i class="bi bi-receipt"></i></button>
        </td>
      </tr>
    `).join(''):'<tr><td colspan="8" class="text-center text-muted py-4">No fee records</td></tr>';
  }catch(e){ toast('Failed to load fees','error'); }
}

async function loadFeeSummary(){
  const sid=document.getElementById('fee-student').value;
  if(!sid) return;
  const d=await api(`/api/fees/summary?student_id=${sid}`);
  document.getElementById('fee-amount').value=d.records.length?d.records[0].amount:'';
}

async function recordPayment(){
  const sid=document.getElementById('fee-student').value;
  const amount=+document.getElementById('fee-amount').value;
  const month=document.getElementById('fee-month').value;
  const mode=document.getElementById('fee-mode').value;
  const discount=+document.getElementById('fee-discount').value||0;
  const fine=+document.getElementById('fee-fine').value||0;
  if(!sid||!amount){ toast('Student and amount required','error'); return; }
  try{
    const r=await api('/api/fees/pay','POST',{student_id:sid,amount,month,payment_mode:mode,discount,fine});
    toast('Payment recorded! Receipt: '+r.receipt_no);
    printReceipt(r.receipt_no, document.getElementById('fee-student').options[document.getElementById('fee-student').selectedIndex].text, month, amount, new Date().toISOString().split('T')[0], mode);
    loadFees();
  }catch(e){ toast(e.message,'error'); }
}

async function markPaid(id){
  try{
    await api('/api/fees/pay','POST',{fee_id:id,payment_mode:'Cash'});
    toast('Marked as paid');
    loadFees();
  }catch(e){ toast(e.message,'error'); }
}

async function generateFees(){
  const month=document.getElementById('gen-month').value;
  const due=document.getElementById('gen-due').value;
  if(!month||!due){ toast('Month and due date required','error'); return; }
  try{
    const r=await api('/api/fees/generate','POST',{month,due_date:due});
    toast(r.message);
    loadFees();
  }catch(e){ toast(e.message,'error'); }
}

function printReceipt(receipt,name,month,amount,date,mode){
  document.getElementById('receipt-content').innerHTML=`
    <div class="receipt-box">
      <div class="text-center mb-3"><h5 class="mb-0">🏢 HOSTEL MANAGEMENT SYSTEM</h5><small>Fee Payment Receipt</small><hr></div>
      <table class="w-100"><tbody>
        <tr><td><b>Receipt No:</b></td><td>${receipt||'N/A'}</td></tr>
        <tr><td><b>Student:</b></td><td>${name}</td></tr>
        <tr><td><b>Month:</b></td><td>${month}</td></tr>
        <tr><td><b>Amount:</b></td><td>₹${Number(amount).toLocaleString('en-IN')}</td></tr>
        <tr><td><b>Date:</b></td><td>${date}</td></tr>
        <tr><td><b>Mode:</b></td><td>${mode||'Cash'}</td></tr>
        <tr><td><b>Status:</b></td><td><b>PAID ✓</b></td></tr>
      </tbody></table>
      <hr><div class="text-center"><small>Thank you for your payment</small></div>
    </div>`;
  new bootstrap.Modal(document.getElementById('receiptModal')).show();
}

// ── COMPLAINTS ────────────────────────────────────────────────────────────────
async function loadComplaints(){
  const status=document.getElementById('comp-filter').value;
  try{
    const rows=await api(`/api/complaints?status=${status}`);
    document.getElementById('comp-tbody').innerHTML=rows.length?rows.map(r=>`
      <tr>
        <td><div class="fw-semibold">${r.student_name}</div><small class="text-muted">${r.s_id}</small></td>
        <td><span class="badge bg-secondary bg-opacity-15 text-dark">${r.category}</span></td>
        <td>${r.subject}</td>
        <td>${priorityBadge(r.priority)}</td>
        <td>${badge(r.status)}</td>
        <td><small>${r.created_at?.split('T')[0]||r.created_at||''}</small></td>
        <td><button class="btn btn-sm btn-outline-primary" onclick="openCompModal(${r.id},'${r.status}')"><i class="bi bi-pencil"></i></button></td>
      </tr>
    `).join(''):'<tr><td colspan="7" class="text-center text-muted py-4">No complaints</td></tr>';
  }catch(e){ toast('Failed to load complaints','error'); }
}

async function submitComplaint(){
  const sid=document.getElementById('comp-student').value;
  const cat=document.getElementById('comp-category').value;
  const sub=document.getElementById('comp-subject').value;
  const desc=document.getElementById('comp-desc').value;
  const pri=document.getElementById('comp-priority').value;
  if(!sid||!sub){ toast('Student and subject required','error'); return; }
  try{
    await api('/api/complaints','POST',{student_id:sid,category:cat,subject:sub,description:desc,priority:pri});
    toast('Complaint registered');
    document.getElementById('comp-subject').value='';
    document.getElementById('comp-desc').value='';
    loadComplaints();
    loadDashboard();
  }catch(e){ toast(e.message,'error'); }
}

function openCompModal(id,status){
  document.getElementById('comp-update-id').value=id;
  document.getElementById('comp-update-status').value=status;
  document.getElementById('comp-update-remark').value='';
  new bootstrap.Modal(document.getElementById('compModal')).show();
}

async function updateComplaint(){
  const id=document.getElementById('comp-update-id').value;
  const status=document.getElementById('comp-update-status').value;
  const remarks=document.getElementById('comp-update-remark').value;
  try{
    await api(`/api/complaints/${id}`,'PUT',{status,remarks});
    bootstrap.Modal.getInstance(document.getElementById('compModal')).hide();
    toast('Complaint updated');
    loadComplaints(); loadDashboard();
  }catch(e){ toast(e.message,'error'); }
}

// ── NOTICES ───────────────────────────────────────────────────────────────────
async function loadNotices(){
  try{
    const rows=await api('/api/notices');
    const colors={'High':'danger','Urgent':'danger','Normal':'primary','General':'secondary'};
    document.getElementById('notices-grid').innerHTML=rows.length?rows.map(r=>`
      <div class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <span class="badge bg-${colors[r.priority]||'secondary'} mb-1">${r.priority}</span>
              <span class="badge bg-light text-dark ms-1 mb-1">${r.category}</span>
              <h6 class="mb-1">${r.title}</h6>
              <p class="text-muted mb-1" style="font-size:.875rem">${r.content}</p>
              <small class="text-muted"><i class="bi bi-calendar me-1"></i>${r.created_at?.split('T')[0]||''} ${r.expires_at?`· Expires: ${r.expires_at}`:''}</small>
            </div>
            <button class="btn btn-sm btn-outline-danger ms-2" onclick="deleteNotice(${r.id})"><i class="bi bi-trash"></i></button>
          </div>
        </div>
      </div>
    `).join(''):'<div class="text-center text-muted py-5"><i class="bi bi-megaphone display-4 d-block mb-2"></i>No active notices</div>';
  }catch(e){ toast('Failed to load notices','error'); }
}

async function postNotice(){
  const title=document.getElementById('notice-title').value;
  const content=document.getElementById('notice-content').value;
  if(!title||!content){ toast('Title and content required','error'); return; }
  try{
    await api('/api/notices','POST',{
      title,content,
      category:document.getElementById('notice-cat').value,
      priority:document.getElementById('notice-priority').value,
      expires_at:document.getElementById('notice-expires').value||null
    });
    toast('Notice posted');
    document.getElementById('notice-title').value='';
    document.getElementById('notice-content').value='';
    loadNotices();
  }catch(e){ toast(e.message,'error'); }
}

async function deleteNotice(id){
  if(!confirm('Remove this notice?')) return;
  try{ await api(`/api/notices/${id}`,'DELETE'); toast('Notice removed','info'); loadNotices(); }
  catch(e){ toast(e.message,'error'); }
}

// ── VISITORS ──────────────────────────────────────────────────────────────────
async function loadVisitors(){
  try{
    const rows=await api('/api/visitors');
    document.getElementById('vis-tbody').innerHTML=rows.length?rows.map(r=>`
      <tr>
        <td><strong>${r.visitor_name}</strong></td>
        <td>${r.student_name}<br><small class="text-muted">${r.s_id}</small></td>
        <td>${r.relation||'—'}</td>
        <td>${r.purpose||'—'}</td>
        <td><small>${r.check_in?.replace('T',' ').slice(0,16)||''}</small></td>
        <td>${r.check_out?`<small>${r.check_out?.replace('T',' ').slice(0,16)}</small>`:'<span class="badge badge-active">In</span>'}</td>
        <td>${!r.check_out?`<button class="btn btn-sm btn-outline-warning" onclick="checkOut(${r.id})"><i class="bi bi-box-arrow-right me-1"></i>Out</button>`:''}</td>
      </tr>
    `).join(''):'<tr><td colspan="7" class="text-center text-muted py-4">No visitors</td></tr>';
  }catch(e){ toast('Failed to load visitors','error'); }
}

async function checkInVisitor(){
  const sid=document.getElementById('vis-student').value;
  const name=document.getElementById('vis-name').value;
  if(!sid||!name){ toast('Student and visitor name required','error'); return; }
  try{
    await api('/api/visitors','POST',{
      student_id:sid, visitor_name:name,
      relation:document.getElementById('vis-relation').value,
      phone:document.getElementById('vis-phone').value,
      purpose:document.getElementById('vis-purpose').value
    });
    toast('Visitor checked in');
    ['vis-name','vis-relation','vis-phone','vis-purpose'].forEach(i=>document.getElementById(i).value='');
    loadVisitors();
  }catch(e){ toast(e.message,'error'); }
}

async function checkOut(id){
  try{ await api(`/api/visitors/${id}/checkout`,'POST'); toast('Visitor checked out','info'); loadVisitors(); }
  catch(e){ toast(e.message,'error'); }
}
async function doLogout(){
  await fetch('/api/logout',{method:'POST'});
  window.location.href='/login';
}

// ── VERIFICATIONS ──────────────────────────────────────────────────────────────
async function loadVerifications(){
  try{
    const rows=await api('/api/verifications');
    document.getElementById('verif-tbody').innerHTML=rows.length?rows.map(r=>`
      <tr>
        <td><code>${r.verify_code}</code></td>
        <td><span class="badge ${r.student_type==='fresher'?'bg-primary':'bg-success'} bg-opacity-15 text-${r.student_type==='fresher'?'primary':'success'}">${r.student_type==='fresher'?'Fresher':'Existing'}</span></td>
        <td><strong>${r.name}</strong></td>
        <td>${r.course||'—'}</td>
        <td><small>${r.email||'—'}</small></td>
        <td>${r.is_registered?'<span class="badge badge-paid">Registered</span>':'<span class="badge badge-pending">Pending</span>'}</td>
        <td><small>${r.registered_at?r.registered_at.slice(0,10):'—'}</small></td>
        <td>${!r.is_registered?`<button class="btn btn-sm btn-outline-danger" onclick="delVerif(${r.id})"><i class="bi bi-trash"></i></button>`:''}</td>
      </tr>`).join(''):'<tr><td colspan="8" class="text-center text-muted py-4">No verification records</td></tr>';
  }catch(e){ toast('Failed to load verifications','error'); }
}

async function addVerification(){
  const code=document.getElementById('vf-code').value.trim();
  const name=document.getElementById('vf-name').value.trim();
  if(!code||!name){toast('Code and name are required','error');return;}
  try{
    await api('/api/verifications','POST',{
      verify_code:code, student_type:document.getElementById('vf-type').value,
      name, email:document.getElementById('vf-email').value,
      course:document.getElementById('vf-course').value,
      year:+document.getElementById('vf-year').value,
      gender:document.getElementById('vf-gender').value
    });
    toast('Verification record added! Student can now register.');
    ['vf-code','vf-name','vf-email','vf-course'].forEach(i=>document.getElementById(i).value='');
    loadVerifications();
  }catch(e){ toast(e.message,'error'); }
}

async function delVerif(id){
  if(!confirm('Delete this verification code?')) return;
  try{ await api(`/api/verifications/${id}`,'DELETE'); toast('Deleted','info'); loadVerifications(); }
  catch(e){ toast(e.message,'error'); }
}
</script>
</body>
</html>"""

# ─── LOGIN PAGE HTML ─────────────────────────────────────────────────────────
LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HostelMS &mdash; Sign In</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{min-height:100vh;display:flex;font-family:'Segoe UI',system-ui,sans-serif;background:#f8fafc;}
/* Left panel */
.lp{width:42%;flex-shrink:0;background:linear-gradient(160deg,#1e1b4b 0%,#312e81 52%,#4338ca 100%);display:flex;flex-direction:column;justify-content:center;padding:48px 44px;position:relative;overflow:hidden;}
.lp::before{content:'';position:absolute;inset:0;opacity:.06;background-image:radial-gradient(circle,#fff 1px,transparent 1px);background-size:28px 28px;}
.logo-box{width:58px;height:58px;background:rgba(255,255,255,.15);border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:1.7rem;margin-bottom:22px;}
.app-name{color:#fff;font-size:2.1rem;font-weight:800;letter-spacing:-.03em;line-height:1.1;}
.app-sub{color:#a5b4fc;font-size:.88rem;margin:6px 0 38px;}
.feat{display:flex;flex-direction:column;gap:14px;}
.fi{display:flex;align-items:flex-start;gap:13px;}
.fic{width:36px;height:36px;border-radius:10px;background:rgba(255,255,255,.1);display:flex;align-items:center;justify-content:center;font-size:1rem;color:#c7d2fe;flex-shrink:0;margin-top:1px;}
.fit strong{color:#fff;display:block;font-size:.85rem;}
.fit span{color:#a5b4fc;font-size:.79rem;line-height:1.4;}
.kpis{display:flex;gap:12px;margin-top:38px;}
.kpi{flex:1;background:rgba(255,255,255,.08);border-radius:12px;padding:14px 10px;text-align:center;}
.kpi-n{color:#fff;font-size:1.55rem;font-weight:800;line-height:1;}
.kpi-l{color:#a5b4fc;font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;margin-top:3px;}
/* Right panel */
.rp{flex:1;display:flex;align-items:center;justify-content:center;padding:40px 32px;}
.fw{width:100%;max-width:400px;}
.fw h2{font-size:1.7rem;font-weight:800;color:#0f172a;letter-spacing:-.025em;margin-bottom:3px;}
.fw .sub{color:#64748b;font-size:.88rem;margin-bottom:30px;}
.lbl{font-size:.76rem;font-weight:700;color:#374151;display:block;margin-bottom:6px;letter-spacing:.03em;text-transform:uppercase;}
.finp{position:relative;margin-bottom:16px;}
.finp i{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:#94a3b8;font-size:.9rem;pointer-events:none;}
.finp input{width:100%;padding:11px 14px 11px 38px;border:1.5px solid #e2e8f0;border-radius:10px;font-size:.9rem;color:#1e293b;background:#fff;transition:border-color .2s,box-shadow .2s;outline:none;}
.finp input:focus{border-color:#4f46e5;box-shadow:0 0 0 3px rgba(79,70,229,.12);}
.finp input::placeholder{color:#cbd5e1;}
.btn-si{width:100%;padding:12px;background:linear-gradient(135deg,#4f46e5,#6d28d9);border:none;border-radius:10px;color:#fff;font-size:.95rem;font-weight:700;cursor:pointer;transition:.2s;display:flex;align-items:center;justify-content:center;gap:8px;margin-top:4px;}
.btn-si:hover{filter:brightness(1.09);transform:translateY(-1px);box-shadow:0 6px 20px rgba(79,70,229,.3);}
.btn-si:active{transform:none;box-shadow:none;}
.err{background:#fef2f2;border:1px solid #fecaca;border-radius:9px;padding:10px 14px;font-size:.82rem;color:#b91c1c;margin-bottom:14px;display:none;align-items:center;gap:8px;}
.divider{display:flex;align-items:center;gap:10px;margin:22px 0 14px;}
.divider hr{flex:1;border:none;border-top:1px solid #e2e8f0;}
.divider span{font-size:.7rem;color:#94a3b8;font-weight:600;white-space:nowrap;letter-spacing:.05em;}
.cgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.cc{background:#fff;border:1.5px solid #e2e8f0;border-radius:10px;padding:10px 11px;cursor:pointer;transition:.18s;display:flex;align-items:center;gap:8px;}
.cc:hover{border-color:#4f46e5;background:#f5f3ff;transform:translateY(-1px);}
.cb{font-size:.6rem;font-weight:700;padding:2px 7px;border-radius:20px;flex-shrink:0;}
.ca{background:#ede9fe;color:#5b21b6;}
.cs{background:#dcfce7;color:#166534;}
.cu{font-size:.8rem;font-weight:700;color:#1e293b;display:block;}
.cp{font-size:.7rem;color:#64748b;display:block;}
.reg{text-align:center;margin-top:18px;font-size:.82rem;color:#64748b;}
.reg a{color:#4f46e5;font-weight:700;text-decoration:none;}
.reg a:hover{text-decoration:underline;}
@media(max-width:760px){body{flex-direction:column;}.lp{width:100%;padding:30px 22px;}.feat{display:grid;grid-template-columns:1fr 1fr;gap:10px;}.kpis{margin-top:18px;}.rp{padding:26px 18px;}}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>

<div class="lp">
  <div class="logo-box">&#127968;</div>
  <div class="app-name">HostelMS</div>
  <div class="app-sub">Hostel Room Allocation &amp; Fee Management System</div>
  <div class="feat">
    <div class="fi">
      <div class="fic"><i class="bi bi-building"></i></div>
      <div class="fit"><strong>Room Management</strong><span>Multi-block allocation with live capacity tracking</span></div>
    </div>
    <div class="fi">
      <div class="fic"><i class="bi bi-cash-coin"></i></div>
      <div class="fit"><strong>Fee Collection</strong><span>Monthly billing, payment modes &amp; receipts</span></div>
    </div>
    <div class="fi">
      <div class="fic"><i class="bi bi-shield-check"></i></div>
      <div class="fit"><strong>Role-Based Access</strong><span>Admin, Warden &amp; Student self-portal</span></div>
    </div>
    <div class="fi">
      <div class="fic"><i class="bi bi-megaphone"></i></div>
      <div class="fit"><strong>Notices &amp; Complaints</strong><span>Real-time hostel communication board</span></div>
    </div>
  </div>
  <div class="kpis">
    <div class="kpi"><div class="kpi-n">107</div><div class="kpi-l">Students</div></div>
    <div class="kpi"><div class="kpi-n">50</div><div class="kpi-l">Rooms</div></div>
    <div class="kpi"><div class="kpi-n">4</div><div class="kpi-l">Blocks</div></div>
  </div>
</div>

<div class="rp">
  <div class="fw">
    <h2>Welcome back &#128075;</h2>
    <p class="sub">Sign in to continue to your dashboard</p>

    <div class="err" id="err-box">
      <i class="bi bi-exclamation-circle-fill"></i>
      <span id="err-txt"></span>
    </div>

    <label class="lbl">Username</label>
    <div class="finp">
      <i class="bi bi-person"></i>
      <input type="text" id="username" placeholder="Enter your username" autofocus>
    </div>

    <label class="lbl">Password</label>
    <div class="finp">
      <i class="bi bi-lock"></i>
      <input type="password" id="password" placeholder="Enter your password" onkeydown="if(event.key==='Enter')doLogin()">
    </div>

    <button class="btn-si" onclick="doLogin()" id="login-btn">
      <i class="bi bi-box-arrow-in-right"></i> Sign In
    </button>

    <div class="divider"><hr><span>QUICK TEST LOGIN</span><hr></div>

    <div class="cgrid">
      <div class="cc" onclick="fill('admin','admin123')">
        <span class="cb ca">ADMIN</span>
        <div><span class="cu">admin</span><span class="cp">admin123 &middot; Full Access</span></div>
      </div>
      <div class="cc" onclick="fill('warden','warden123')">
        <span class="cb ca">ADMIN</span>
        <div><span class="cu">warden</span><span class="cp">warden123 &middot; Full Access</span></div>
      </div>
      <div class="cc" onclick="fill('rahul','rahul123')">
        <span class="cb cs">STUDENT</span>
        <div><span class="cu">rahul</span><span class="cp">rahul123 &middot; My Portal</span></div>
      </div>
      <div class="cc" onclick="fill('aryan','aryan123')">
        <span class="cb cs">STUDENT</span>
        <div><span class="cu">aryan</span><span class="cp">aryan123 &middot; My Portal</span></div>
      </div>
    </div>

    <div class="reg">
      New student? <a href="/register"><i class="bi bi-person-plus"></i> Register with admission code</a>
    </div>
  </div>
</div>

<script>
function fill(u,p){document.getElementById('username').value=u;document.getElementById('password').value=p;}
async function doLogin(){
  const u=document.getElementById('username').value.trim();
  const p=document.getElementById('password').value;
  if(!u||!p){showErr('Please enter both username and password');return;}
  const btn=document.getElementById('login-btn');
  btn.disabled=true;
  btn.innerHTML='<span style="width:15px;height:15px;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;border-radius:50%;display:inline-block;animation:spin .7s linear infinite"></span>&nbsp;Signing in...';
  try{
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    const d=await r.json();
    if(!r.ok){showErr(d.error||'Invalid credentials');resetBtn();return;}
    window.location.href='/';
  }catch(e){showErr('Server error. Please try again.');resetBtn();}
}
function resetBtn(){const b=document.getElementById('login-btn');b.disabled=false;b.innerHTML='<i class="bi bi-box-arrow-in-right"></i> Sign In';}
function showErr(m){const b=document.getElementById('err-box');document.getElementById('err-txt').textContent=m;b.style.display='flex';setTimeout(()=>b.style.display='none',4500);}
</script>
</body></html>"""

# ─── STUDENT PORTAL HTML ─────────────────────────────────────────────────────
STUDENT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Student Portal — HostelMS</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Segoe UI',sans-serif;background:#f1f5f9;color:#1e293b;}
.topbar{background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:14px 24px;display:flex;align-items:center;gap:12px;color:#fff;position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(79,70,229,.3);}
.topbar h5{margin:0;font-weight:700;font-size:1rem;flex:1;}
.content{padding:24px;max-width:900px;margin:0 auto;}
.card{border:none;border-radius:14px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:20px;}
.card-header{background:#fff;border-bottom:1px solid #f1f5f9;border-radius:14px 14px 0 0!important;padding:14px 20px;font-weight:600;font-size:.9rem;}
.stat-card{background:#fff;border-radius:14px;padding:18px 20px;display:flex;align-items:center;gap:14px;box-shadow:0 1px 4px rgba(0,0,0,.07);}
.stat-icon{width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0;}
.stat-card h4{font-size:1.4rem;font-weight:700;margin:0;}
.stat-card p{color:#64748b;font-size:.8rem;margin:0;}
.nav-tabs .nav-link.active{background:#4f46e5;color:#fff;border-color:#4f46e5;border-radius:8px 8px 0 0;}
.nav-tabs .nav-link{color:#475569;border-radius:8px 8px 0 0;}
.badge-paid{background:#dcfce7;color:#166634;}
.badge-pending{background:#fff7ed;color:#c2410c;}
.badge-open{background:#fee2e2;color:#991b1b;}
.badge-resolved{background:#dcfce7;color:#166534;}
.badge-active{background:#dbeafe;color:#1e40af;}
badge-inprogress{background:#fef9c3;color:#854d0e;}
.form-control,.form-select{border-radius:8px;border:1.5px solid #e2e8f0;font-size:.875rem;}
.form-control:focus,.form-select:focus{border-color:#4f46e5;box-shadow:0 0 0 3px rgba(79,70,229,.1);}
.btn-primary{background:#4f46e5;border-color:#4f46e5;}
.notice-card{border-left:4px solid #4f46e5;background:#fff;border-radius:0 12px 12px 0;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.06);}
.notice-card.high{border-left-color:#ef4444;}
.notice-card.urgent{border-left-color:#dc2626;}
#toast-wrap{position:fixed;top:16px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:8px;}
.toast-msg{background:#1e293b;color:#fff;padding:11px 16px;border-radius:10px;font-size:.875rem;min-width:240px;display:flex;align-items:center;gap:8px;animation:fadeIn .25s;}
.toast-msg.success{border-left:4px solid #22c55e;}.toast-msg.error{border-left:4px solid #ef4444;}
@keyframes fadeIn{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:translateX(0)}}
.avatar{width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,.25);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;}
</style>
</head>
<body>
<div class="topbar">
  <i class="bi bi-building-fill fs-5"></i>
  <h5>HostelMS — Student Portal</h5>
  <div class="ms-auto d-flex align-items-center gap-3">
    <span id="user-name" class="small fw-semibold"></span>
    <div class="avatar" id="user-avatar">S</div>
    <button class="btn btn-sm btn-light btn-outline-light" onclick="doLogout()"><i class="bi bi-box-arrow-right me-1"></i>Logout</button>
  </div>
</div>

<div class="content">
  <!-- Stats -->
  <div class="row g-3 mb-4">
    <div class="col-6 col-md-3">
      <div class="stat-card"><div class="stat-icon" style="background:#ede9fe"><i class="bi bi-door-closed-fill" style="color:#7c3aed"></i></div>
      <div><h4 id="my-room">—</h4><p>My Room</p></div></div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card"><div class="stat-icon" style="background:#fff7ed"><i class="bi bi-cash-coin" style="color:#ea580c"></i></div>
      <div><h4 id="my-pending">₹0</h4><p>Pending Fees</p></div></div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card"><div class="stat-icon" style="background:#dcfce7"><i class="bi bi-check-circle-fill" style="color:#16a34a"></i></div>
      <div><h4 id="my-paid">₹0</h4><p>Total Paid</p></div></div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card"><div class="stat-icon" style="background:#fee2e2"><i class="bi bi-chat-dots-fill" style="color:#dc2626"></i></div>
      <div><h4 id="my-complaints">0</h4><p>Complaints</p></div></div>
    </div>
  </div>

  <!-- Tabs -->
  <ul class="nav nav-tabs mb-0" id="myTab">
    <li class="nav-item"><a class="nav-link active" onclick="switchTab('my-info')" id="tab-my-info"><i class="bi bi-person-circle me-1"></i>My Info</a></li>
    <li class="nav-item"><a class="nav-link" onclick="switchTab('my-fees')" id="tab-my-fees"><i class="bi bi-receipt me-1"></i>My Fees</a></li>
    <li class="nav-item"><a class="nav-link" onclick="switchTab('my-complaints')" id="tab-my-complaints"><i class="bi bi-chat-dots me-1"></i>Complaints</a></li>
    <li class="nav-item"><a class="nav-link" onclick="switchTab('notices')" id="tab-notices"><i class="bi bi-megaphone me-1"></i>Notices</a></li>
  </ul>

  <div style="background:#fff;border-radius:0 0 14px 14px;box-shadow:0 1px 4px rgba(0,0,0,.07);padding:20px;">

  <!-- MY INFO -->
  <div id="panel-my-info">
    <div class="row g-3">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header"><i class="bi bi-person-badge me-2 text-primary"></i>Student Profile</div>
          <div class="card-body" id="profile-body"><div class="text-center text-muted py-3">Loading...</div></div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header"><i class="bi bi-door-open me-2 text-success"></i>Room Details</div>
          <div class="card-body" id="room-body"><div class="text-center text-muted py-3">Loading...</div></div>
        </div>
      </div>
    </div>
  </div>

  <!-- MY FEES -->
  <div id="panel-my-fees" style="display:none">
    <div class="table-responsive">
      <table class="table table-hover">
        <thead><tr><th>Receipt</th><th>Month</th><th>Amount</th><th>Due Date</th><th>Paid Date</th><th>Status</th><th>Mode</th></tr></thead>
        <tbody id="my-fees-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- MY COMPLAINTS -->
  <div id="panel-my-complaints" style="display:none">
    <div class="row g-3 mb-3">
      <div class="col-md-5">
        <div class="card">
          <div class="card-header"><i class="bi bi-plus-circle me-2 text-danger"></i>New Complaint</div>
          <div class="card-body">
            <div class="mb-2"><label class="form-label">Category *</label>
              <select class="form-select" id="my-comp-cat">
                <option>Plumbing</option><option>Electricity</option><option>Cleanliness</option>
                <option>Internet</option><option>Furniture</option><option>Food</option><option>Security</option><option>Other</option>
              </select>
            </div>
            <div class="mb-2"><label class="form-label">Priority</label>
              <select class="form-select" id="my-comp-pri"><option>Low</option><option selected>Medium</option><option>High</option></select>
            </div>
            <div class="mb-2"><label class="form-label">Subject *</label>
              <input type="text" class="form-control" id="my-comp-sub" placeholder="Brief subject">
            </div>
            <div class="mb-3"><label class="form-label">Description</label>
              <textarea class="form-control" id="my-comp-desc" rows="3" placeholder="Describe the issue..."></textarea>
            </div>
            <button class="btn btn-danger w-100" onclick="submitMyComplaint()"><i class="bi bi-send me-1"></i>Submit Complaint</button>
          </div>
        </div>
      </div>
      <div class="col-md-7">
        <h6 class="mb-2 text-muted">My Complaints</h6>
        <div id="my-comp-list"></div>
      </div>
    </div>
  </div>

  <!-- NOTICES -->
  <div id="panel-notices" style="display:none">
    <div id="notices-list"></div>
  </div>

  </div>
</div>

<div id="toast-wrap"></div>

<script>
let ME = {};

async function init(){
  const r = await fetch('/api/me');
  if(!r.ok){ window.location.href='/login'; return; }
  ME = await r.json();
  document.getElementById('user-name').textContent = ME.name || ME.username;
  document.getElementById('user-avatar').textContent = (ME.name||ME.username).charAt(0).toUpperCase();
  loadMyInfo();
  loadSummary();
}

function toast(msg,type='success'){
  const el=document.createElement('div');
  el.className=`toast-msg ${type}`;
  el.innerHTML=`<i class="bi ${type==='success'?'bi-check-circle':'bi-x-circle'}-fill"></i>${msg}`;
  document.getElementById('toast-wrap').appendChild(el);
  setTimeout(()=>el.remove(),3500);
}

async function api(url,method='GET',body=null){
  const opts={method,headers:{'Content-Type':'application/json'}};
  if(body) opts.body=JSON.stringify(body);
  const r=await fetch(url,opts);
  const d=await r.json();
  if(!r.ok) throw new Error(d.error||'Error');
  return d;
}

function badge(v){
  const m={'Paid':'paid','Pending':'pending','Open':'open','Resolved':'resolved','Active':'active','In Progress':'inprogress'};
  return `<span class="badge badge-${m[v]||'active'}">${v}</span>`;
}

function switchTab(name){
  ['my-info','my-fees','my-complaints','notices'].forEach(t=>{
    document.getElementById('panel-'+t).style.display='none';
    document.getElementById('tab-'+t).classList.remove('active');
  });
  document.getElementById('panel-'+name).style.display='block';
  document.getElementById('tab-'+name).classList.add('active');
  if(name==='my-fees') loadMyFees();
  if(name==='my-complaints') loadMyComplaints();
  if(name==='notices') loadNotices();
}

async function loadSummary(){
  try{
    const fees = await api(`/api/fees?student_id=${ME.student_id}`);
    const pending = fees.filter(f=>f.status==='Pending').reduce((s,f)=>s+f.amount,0);
    const paid    = fees.filter(f=>f.status==='Paid').reduce((s,f)=>s+f.amount,0);
    document.getElementById('my-pending').textContent='₹'+pending.toLocaleString('en-IN');
    document.getElementById('my-paid').textContent='₹'+paid.toLocaleString('en-IN');
    const comps = await api(`/api/complaints?student_id=${ME.student_id}`);
    document.getElementById('my-complaints').textContent=comps.length;
  }catch(e){}
}

async function loadMyInfo(){
  try{
    const s = await api(`/api/students/${ME.student_id}`);
    document.getElementById('my-room').textContent = s.allocation && s.allocation.room_no ? s.allocation.room_no : '—';
    document.getElementById('profile-body').innerHTML=`
      <table class="table table-sm table-borderless mb-0">
        <tr><th style="width:40%;color:#64748b">Student ID</th><td><strong>${s.student_id}</strong></td></tr>
        <tr><th style="color:#64748b">Full Name</th><td>${s.name}</td></tr>
        <tr><th style="color:#64748b">Email</th><td>${s.email}</td></tr>
        <tr><th style="color:#64748b">Phone</th><td>${s.phone||'—'}</td></tr>
        <tr><th style="color:#64748b">Gender</th><td>${s.gender||'—'}</td></tr>
        <tr><th style="color:#64748b">Course</th><td>${s.course||'—'}</td></tr>
        <tr><th style="color:#64748b">Year</th><td>${s.year||'—'}</td></tr>
        <tr><th style="color:#64748b">Guardian</th><td>${s.guardian_name||'—'}</td></tr>
        <tr><th style="color:#64748b">Guardian Ph</th><td>${s.guardian_phone||'—'}</td></tr>
      </table>`;
    if(s.allocation && s.allocation.room_no){
      document.getElementById('room-body').innerHTML=`
        <table class="table table-sm table-borderless mb-0">
          <tr><th style="width:45%;color:#64748b">Room No</th><td><strong>${s.allocation.room_no}</strong></td></tr>
          <tr><th style="color:#64748b">Block</th><td>${s.allocation.block}</td></tr>
          <tr><th style="color:#64748b">Floor</th><td>${s.allocation.floor}</td></tr>
          <tr><th style="color:#64748b">Monthly Rent</th><td><strong>₹${s.allocation.rent?.toLocaleString('en-IN')}</strong></td></tr>
          <tr><th style="color:#64748b">From Date</th><td>${s.allocation.allocated_date}</td></tr>
          <tr><th style="color:#64748b">Exp. Vacate</th><td>${s.allocation.expected_vacate||'—'}</td></tr>
          <tr><th style="color:#64748b">Status</th><td><span class="badge badge-active">Active</span></td></tr>
        </table>`;
    } else {
      document.getElementById('room-body').innerHTML='<div class="text-center text-muted py-4"><i class="bi bi-door-closed display-5 d-block mb-2"></i>No room allocated yet</div>';
    }
  }catch(e){ document.getElementById('profile-body').innerHTML='<p class="text-danger">Failed to load profile</p>'; }
}

async function loadMyFees(){
  try{
    const fees = await api(`/api/fees?student_id=${ME.student_id}`);
    document.getElementById('my-fees-tbody').innerHTML = fees.length ? fees.map(f=>`
      <tr>
        <td><small class="font-monospace">${f.receipt_no||'—'}</small></td>
        <td>${f.month||'—'}</td>
        <td>₹${f.amount.toLocaleString('en-IN')}</td>
        <td><small>${f.due_date}</small></td>
        <td><small>${f.paid_date||'—'}</small></td>
        <td>${badge(f.status)}</td>
        <td><small>${f.payment_mode||'—'}</small></td>
      </tr>`).join('') : '<tr><td colspan="7" class="text-center text-muted py-4">No fee records</td></tr>';
  }catch(e){ toast('Failed to load fees','error'); }
}

async function loadMyComplaints(){
  try{
    const rows = await api(`/api/complaints?student_id=${ME.student_id}`);
    const colors={'High':'danger','Medium':'warning','Low':'success'};
    document.getElementById('my-comp-list').innerHTML = rows.length ? rows.map(r=>`
      <div class="card mb-2">
        <div class="card-body py-2 px-3">
          <div class="d-flex justify-content-between align-items-start">
            <div><span class="badge bg-secondary bg-opacity-15 text-dark me-1">${r.category}</span><span class="badge bg-${colors[r.priority]||'secondary'} bg-opacity-15 text-${colors[r.priority]||'secondary'}">  ${r.priority}</span>
            <div class="fw-semibold mt-1" style="font-size:.875rem">${r.subject}</div>
            <small class="text-muted">${r.created_at?.split('T')[0]||r.created_at||''}</small></div>
            <div>${badge(r.status)}</div>
          </div>
          ${r.remarks?`<div class="mt-1 p-2 bg-light rounded"><small><b>Remark:</b> ${r.remarks}</small></div>`:''}
        </div>
      </div>`).join('') : '<p class="text-muted text-center py-3">No complaints yet</p>';
  }catch(e){}
}

async function submitMyComplaint(){
  const sub=document.getElementById('my-comp-sub').value.trim();
  if(!sub){ toast('Subject is required','error'); return; }
  try{
    await api('/api/complaints','POST',{
      student_id: ME.student_id,
      category: document.getElementById('my-comp-cat').value,
      priority: document.getElementById('my-comp-pri').value,
      subject: sub,
      description: document.getElementById('my-comp-desc').value
    });
    toast('Complaint submitted!');
    document.getElementById('my-comp-sub').value='';
    document.getElementById('my-comp-desc').value='';
    loadMyComplaints();
    loadSummary();
  }catch(e){ toast(e.message,'error'); }
}

async function loadNotices(){
  try{
    const rows = await api('/api/notices');
    const colors={'High':'high','Urgent':'urgent','Normal':'','Emergency':'urgent'};
    document.getElementById('notices-list').innerHTML = rows.length ? rows.map(r=>`
      <div class="notice-card ${colors[r.priority]||''}">
        <div class="d-flex justify-content-between">
          <div>
            <span class="badge bg-primary bg-opacity-15 text-primary me-1">${r.category}</span>
            <span class="badge bg-secondary bg-opacity-10 text-dark">${r.priority}</span>
          </div>
          <small class="text-muted">${r.created_at?.split('T')[0]||''}</small>
        </div>
        <h6 class="mt-2 mb-1">${r.title}</h6>
        <p class="mb-0 text-muted" style="font-size:.875rem">${r.content}</p>
        ${r.expires_at?`<small class="text-muted">Expires: ${r.expires_at}</small>`:''}
      </div>`).join('') : '<div class="text-center text-muted py-5"><i class="bi bi-megaphone display-4 d-block mb-2"></i>No active notices</div>';
  }catch(e){}
}

async function doLogout(){
  await fetch('/api/logout',{method:'POST'});
  window.location.href='/login';
}

document.addEventListener('DOMContentLoaded', init);
</script>
</body></html>"""

# ─── REGISTER PAGE HTML ───────────────────────────────────────────────────────
REGISTER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Student Registration — HostelMS</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{min-height:100vh;background:linear-gradient(135deg,#1e1b4b 0%,#312e81 45%,#4f46e5 100%);display:flex;align-items:flex-start;justify-content:center;font-family:'Segoe UI',sans-serif;padding:30px 16px;}
.reg-card{background:#fff;border-radius:20px;padding:34px 32px 28px;width:100%;max-width:560px;box-shadow:0 24px 60px rgba(0,0,0,.35);}
.brand{text-align:center;margin-bottom:20px;}
.brand .icon{width:54px;height:54px;background:linear-gradient(135deg,#4f46e5,#7c3aed);border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 10px;}
.brand h4{font-weight:700;color:#1e293b;font-size:1.15rem;margin:0;}
.brand p{color:#64748b;font-size:.8rem;margin:2px 0 0;}
.step-bar{display:flex;align-items:center;margin-bottom:22px;}
.step-item{flex:1;text-align:center;}
.sc{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700;margin:0 auto 3px;transition:.3s;}
.sc.act{background:#4f46e5;color:#fff;box-shadow:0 0 0 3px rgba(79,70,229,.2);}
.sc.done{background:#22c55e;color:#fff;}
.sc.pend{background:#e2e8f0;color:#94a3b8;}
.sl{flex:0 0 40px;height:2px;background:#e2e8f0;margin-bottom:16px;transition:.4s;}
.sl.done{background:#22c55e;}
.step-label{font-size:.67rem;color:#64748b;font-weight:600;text-transform:uppercase;}
.err{background:#fee2e2;color:#991b1b;border-radius:8px;padding:10px 14px;font-size:.83rem;margin-bottom:14px;display:none;}
.form-label{font-size:.8rem;font-weight:600;color:#374151;margin-bottom:4px;}
.form-control,.form-select{border-radius:9px;border:1.5px solid #e2e8f0;font-size:.875rem;}
.form-control:focus,.form-select:focus{border-color:#4f46e5;box-shadow:0 0 0 3px rgba(79,70,229,.1);outline:none;}
.btn-main{background:linear-gradient(135deg,#4f46e5,#7c3aed);border:none;border-radius:10px;padding:11px 16px;font-weight:600;font-size:.9rem;color:#fff;transition:.2s;}
.btn-main:hover{opacity:.9;transform:translateY(-1px);color:#fff;}
.btn-back{background:#f1f5f9;border:none;border-radius:10px;padding:11px 16px;font-weight:600;color:#475569;}
.btn-back:hover{background:#e2e8f0;}
.type-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:18px;}
.type-btn{padding:14px 10px;border-radius:12px;border:2px solid #e2e8f0;background:#fff;cursor:pointer;text-align:center;transition:.2s;}
.type-btn:hover{border-color:#a5b4fc;}
.type-btn.sel{border-color:#4f46e5;background:#ede9fe;}
.type-btn i{display:block;font-size:1.6rem;color:#94a3b8;margin-bottom:5px;}
.type-btn.sel i{color:#4f46e5;}
.type-btn strong{display:block;font-size:.83rem;color:#1e293b;}
.type-btn small{font-size:.73rem;color:#64748b;}
.ok-bar{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:11px 14px;margin-bottom:14px;}
.ok-bar b{color:#166534;font-size:.83rem;}
.ok-bar p{color:#15803d;font-size:.78rem;margin:2px 0 0;}
.success-box{text-align:center;padding:16px 0;}
.check-icon{width:70px;height:70px;background:#dcfce7;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.9rem;color:#16a34a;margin:0 auto 14px;}
</style></head>
<body><div class="reg-card">
  <div class="brand">
    <div class="icon"><i class="bi bi-building-fill text-white" style="font-size:1.4rem"></i></div>
    <h4>HostelMS — Student Registration</h4>
    <p>Self-register using your admission or roll number</p>
  </div>

  <div class="step-bar" id="step-bar">
    <div class="step-item"><div class="sc act" id="sc1">1</div><div class="step-label">Verify</div></div>
    <div class="sl" id="sl1"></div>
    <div class="step-item"><div class="sc pend" id="sc2">2</div><div class="step-label">Profile</div></div>
    <div class="sl" id="sl2"></div>
    <div class="step-item"><div class="sc pend" id="sc3">3</div><div class="step-label">Account</div></div>
  </div>

  <div class="err" id="err-msg"><i class="bi bi-exclamation-triangle me-1"></i><span id="err-txt"></span></div>

  <!-- STEP 1: Verify -->
  <div id="s1">
    <p style="font-size:.83rem;color:#64748b;margin-bottom:14px">Choose your student type and enter the verification code provided by the hostel administration.</p>
    <div class="type-grid">
      <div class="type-btn sel" id="btn-f" onclick="selType('fresher')">
        <i class="bi bi-person-plus-fill"></i>
        <strong>Fresher</strong><small>Admission / Counselling Receipt No.</small>
      </div>
      <div class="type-btn" id="btn-e" onclick="selType('existing')">
        <i class="bi bi-person-badge-fill"></i>
        <strong>Existing Student</strong><small>Student Roll No.</small>
      </div>
    </div>
    <div class="mb-3">
      <label class="form-label" id="code-lbl"><i class="bi bi-shield-lock me-1"></i>Admission / Counselling Receipt No. *</label>
      <input class="form-control" id="vcode" placeholder="e.g. ADM2026001" onkeydown="if(event.key==='Enter')verifyCode()">
    </div>
    <button class="btn btn-main w-100" onclick="verifyCode()" id="vbtn"><i class="bi bi-shield-check me-2"></i>Verify Identity</button>
    <p class="text-center mt-3" style="font-size:.82rem;color:#94a3b8">Already registered? <a href="/login" style="color:#4f46e5;font-weight:600">Sign In</a></p>
  </div>

  <!-- STEP 2: Profile -->
  <div id="s2" style="display:none">
    <div class="ok-bar"><b><i class="bi bi-check-circle-fill me-1"></i>Identity Verified!</b><p id="ok-msg">Complete your profile below.</p></div>
    <div class="row g-2">
      <div class="col-md-6"><label class="form-label">Full Name *</label><input class="form-control" id="rn"></div>
      <div class="col-md-6"><label class="form-label">Email *</label><input type="email" class="form-control" id="re"></div>
      <div class="col-md-6"><label class="form-label">Phone</label><input class="form-control" id="rp" placeholder="10-digit number"></div>
      <div class="col-md-6"><label class="form-label">Gender</label>
        <select class="form-select" id="rg"><option>Male</option><option>Female</option><option>Other</option></select></div>
      <div class="col-md-6"><label class="form-label">Date of Birth</label><input type="date" class="form-control" id="rd"></div>
      <div class="col-md-6"><label class="form-label">Course</label><input class="form-control" id="rc" placeholder="B.Tech CSE"></div>
      <div class="col-md-6"><label class="form-label">Year</label>
        <select class="form-select" id="ry"><option value="1">1st Year</option><option value="2">2nd Year</option><option value="3">3rd Year</option><option value="4">4th Year</option></select></div>
      <div class="col-md-6"><label class="form-label">Guardian Name</label><input class="form-control" id="rgn"></div>
      <div class="col-md-6"><label class="form-label">Guardian Phone</label><input class="form-control" id="rgp"></div>
      <div class="col-12"><label class="form-label">Permanent Address</label><textarea class="form-control" id="ra" rows="2"></textarea></div>
    </div>
    <div class="d-flex gap-2 mt-3">
      <button class="btn btn-back" onclick="goStep(1)"><i class="bi bi-arrow-left"></i></button>
      <button class="btn btn-main flex-grow-1" onclick="goStep(3)"><i class="bi bi-arrow-right me-1"></i>Next: Create Account</button>
    </div>
  </div>

  <!-- STEP 3: Account -->
  <div id="s3" style="display:none">
    <p style="font-size:.83rem;color:#64748b;margin-bottom:16px">Create your login credentials for the student portal.</p>
    <div class="mb-3"><label class="form-label"><i class="bi bi-person me-1"></i>Username *</label>
      <input class="form-control" id="ru" placeholder="Choose a unique username">
      <div class="form-text">Use letters, numbers, underscores only.</div>
    </div>
    <div class="mb-3"><label class="form-label"><i class="bi bi-lock me-1"></i>Password *</label>
      <input type="password" class="form-control" id="rpw" placeholder="At least 6 characters"></div>
    <div class="mb-3"><label class="form-label"><i class="bi bi-lock-fill me-1"></i>Confirm Password *</label>
      <input type="password" class="form-control" id="rpw2" onkeydown="if(event.key==='Enter')doRegister()"></div>
    <div class="d-flex gap-2">
      <button class="btn btn-back" onclick="goStep(2)"><i class="bi bi-arrow-left"></i></button>
      <button class="btn btn-main flex-grow-1" onclick="doRegister()" id="rbtn"><i class="bi bi-person-check me-2"></i>Complete Registration</button>
    </div>
  </div>

  <!-- SUCCESS -->
  <div id="s4" style="display:none">
    <div class="success-box">
      <div class="check-icon"><i class="bi bi-check-lg"></i></div>
      <h5 class="fw-bold">Registration Successful! 🎉</h5>
      <p class="text-muted mt-2 mb-4">Your hostel account is ready. Login to view your room, fees and notices.</p>
      <a href="/login" class="btn btn-main px-5"><i class="bi bi-box-arrow-in-right me-2"></i>Go to Login</a>
    </div>
  </div>
</div>

<script>
let VD={}; let ST='fresher';
function selType(t){
  ST=t;
  document.getElementById('btn-f').classList.toggle('sel',t==='fresher');
  document.getElementById('btn-e').classList.toggle('sel',t==='existing');
  document.getElementById('code-lbl').innerHTML=t==='fresher'
    ?'<i class="bi bi-shield-lock me-1"></i>Admission / Counselling Receipt No. *'
    :'<i class="bi bi-shield-lock me-1"></i>Student Roll No. *';
  document.getElementById('vcode').placeholder=t==='fresher'?'e.g. ADM2026001':'e.g. S001';
}
function showErr(m){const e=document.getElementById('err-msg');document.getElementById('err-txt').textContent=m;e.style.display='block';setTimeout(()=>e.style.display='none',5000);}
function goStep(n){
  [1,2,3,4].forEach(i=>{const el=document.getElementById('s'+i);if(el)el.style.display=i===n?'block':'none';});
  for(let i=1;i<=3;i++){
    const sc=document.getElementById('sc'+i);
    if(i<n){sc.className='sc done';sc.innerHTML='<i class="bi bi-check-lg"></i>';}
    else if(i===n){sc.className='sc act';sc.innerHTML=i;}
    else{sc.className='sc pend';sc.innerHTML=i;}
  }
  for(let i=1;i<=2;i++) document.getElementById('sl'+i).className='sl'+(i<n?' done':'');
  if(n===4) document.getElementById('step-bar').style.display='none';
  document.getElementById('err-msg').style.display='none';
}
async function verifyCode(){
  const code=document.getElementById('vcode').value.trim();
  if(!code){showErr('Please enter your verification code');return;}
  const btn=document.getElementById('vbtn');
  btn.disabled=true;btn.innerHTML='<span class="spinner-border spinner-border-sm me-2"></span>Verifying...';
  try{
    const r=await fetch('/api/verify-identity',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({verify_code:code})});
    const d=await r.json();
    if(!r.ok){showErr(d.error||'Verification failed');btn.disabled=false;btn.innerHTML='<i class="bi bi-shield-check me-2"></i>Verify Identity';return;}
    VD=d;
    document.getElementById('rn').value=d.name||'';
    document.getElementById('re').value=d.email||'';
    document.getElementById('rc').value=d.course||'';
    document.getElementById('ry').value=String(d.year||'1');
    document.getElementById('rg').value=d.gender||'Male';
    document.getElementById('ok-msg').textContent='Welcome, '+d.name+'! Your '+(d.student_type==='fresher'?'admission number':'roll number')+' has been verified. Please complete your profile.';
    goStep(2);
  }catch(e){showErr('Server error. Please try again.');btn.disabled=false;btn.innerHTML='<i class="bi bi-shield-check me-2"></i>Verify Identity';}
}
async function doRegister(){
  const u=document.getElementById('ru').value.trim();
  const pw=document.getElementById('rpw').value;
  const pw2=document.getElementById('rpw2').value;
  if(!u){showErr('Username is required');return;}
  if(!pw){showErr('Password is required');return;}
  if(pw!==pw2){showErr('Passwords do not match');return;}
  if(pw.length<6){showErr('Password must be at least 6 characters');return;}
  const data={verify_code:VD.verify_code,username:u,password:pw,
    name:document.getElementById('rn').value,email:document.getElementById('re').value,
    phone:document.getElementById('rp').value,gender:document.getElementById('rg').value,
    dob:document.getElementById('rd').value,course:document.getElementById('rc').value,
    year:+document.getElementById('ry').value,address:document.getElementById('ra').value,
    guardian_name:document.getElementById('rgn').value,guardian_phone:document.getElementById('rgp').value};
  const btn=document.getElementById('rbtn');
  btn.disabled=true;btn.innerHTML='<span class="spinner-border spinner-border-sm me-2"></span>Creating account...';
  try{
    const r=await fetch('/api/self-register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const d=await r.json();
    if(!r.ok){showErr(d.error||'Registration failed');btn.disabled=false;btn.innerHTML='<i class="bi bi-person-check me-2"></i>Complete Registration';return;}
    goStep(4);
  }catch(e){showErr('Server error. Please try again.');btn.disabled=false;btn.innerHTML='<i class="bi bi-person-check me-2"></i>Complete Registration';}
}
</script>
</body></html>"""

# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("✅ Hostel Management System — Real World Edition")
    print("🌐 Open: http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
