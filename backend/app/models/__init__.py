from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student")
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)
    guardian_name = db.Column(db.String(100), nullable=True)
    guardian_phone = db.Column(db.String(20), nullable=True)
    course = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default="Active")
    photo_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_no = db.Column(db.String(20), unique=True, nullable=False)
    block = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer, default=1, nullable=False)
    type = db.Column(db.String(20), default="Single")
    capacity = db.Column(db.Integer, default=1, nullable=False)
    occupied = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="Available")
    rent = db.Column(db.Float, nullable=False)
    deposit = db.Column(db.Float, default=0)
    amenities = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Allocation(db.Model):
    __tablename__ = 'allocations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    allocated_date = db.Column(db.Date, nullable=False)
    vacate_date = db.Column(db.Date, nullable=True)
    expected_vacate = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="Active")
    remarks = db.Column(db.Text, nullable=True)

class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    month = db.Column(db.String(20), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    fine = db.Column(db.Float, default=0)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="Pending")
    payment_mode = db.Column(db.String(50), nullable=True)
    receipt_no = db.Column(db.String(50), unique=True, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="Open")
    priority = db.Column(db.String(20), default="Medium")
    resolved_at = db.Column(db.DateTime, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notice(db.Model):
    __tablename__ = 'notices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    priority = db.Column(db.String(20), default="Normal")
    active = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.Date, nullable=True)

class Visitor(db.Model):
    __tablename__ = 'visitors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    visitor_name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    purpose = db.Column(db.Text, nullable=True)
    check_in = db.Column(db.DateTime, default=datetime.utcnow)
    check_out = db.Column(db.DateTime, nullable=True)

class StudentVerification(db.Model):
    __tablename__ = 'student_verifications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    verify_code = db.Column(db.String(100), unique=True, nullable=False)
    student_type = db.Column(db.String(50), default='fresher')
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    course = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer, default=1)
    gender = db.Column(db.String(10), default='Male')
    is_registered = db.Column(db.Integer, default=0)
    registered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
