from flask import Flask, jsonify, request
from flask_cors import CORS
from database import db
import datetime

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "message": "Hostel Management System API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "rooms": "/rooms",
            "students": "/students",
            "allocations": "/allocations",
            "fees": "/fees",
            "analytics": "/analytics"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    db_status = "Connected" if db.health_check() else "Disconnected"
    return jsonify({
        "status": "Running",
        "database": db_status,
        "timestamp": datetime.datetime.now().isoformat()
    })

# Room Management
@app.route('/rooms', methods=['GET'])
def get_rooms():
    status = request.args.get('status')
    
    if status:
        query = "SELECT * FROM rooms WHERE status = %s ORDER BY block, floor, room_no"
        rooms = db.execute_query(query, (status,))
    else:
        query = "SELECT * FROM rooms ORDER BY block, floor, room_no"
        rooms = db.execute_query(query)
    
    return jsonify(rooms)

@app.route('/rooms/available', methods=['GET'])
def get_available_rooms():
    query = """
        SELECT * FROM rooms 
        WHERE occupied < capacity AND status = 'Available'
        ORDER BY block, floor, room_no
    """
    rooms = db.execute_query(query)
    return jsonify(rooms)

# Student Management
@app.route('/students', methods=['GET'])
def get_students():
    query = "SELECT * FROM students ORDER BY created_at DESC"
    students = db.execute_query(query)
    return jsonify(students)

@app.route('/students', methods=['POST'])
def add_student():
    data = request.json
    query = """
        INSERT INTO students (student_id, name, email, phone, gender, course, year)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    student_id = db.execute_query(query, (
        data['student_id'], data['name'], data['email'], 
        data['phone'], data['gender'], data['course'], data['year']
    ))
    
    return jsonify({
        "message": "Student added successfully",
        "student_id": student_id
    }), 201

# Room Allocation
@app.route('/allocations', methods=['GET'])
def get_allocations():
    query = """
        SELECT a.*, s.name as student_name, s.student_id, r.room_no, r.block
        FROM allocations a
        JOIN students s ON a.student_id = s.id
        JOIN rooms r ON a.room_id = r.id
        ORDER BY a.allocated_date DESC
    """
    allocations = db.execute_query(query)
    return jsonify(allocations)

@app.route('/allocations/allocate', methods=['POST'])
def allocate_room():
    data = request.json
    student_id = data['student_id']
    room_id = data['room_id']
    
    # Check if student already has active allocation
    check_query = "SELECT * FROM allocations WHERE student_id = %s AND status = 'Active'"
    existing = db.execute_query(check_query, (student_id,))
    
    if existing:
        return jsonify({"error": "Student already has an active allocation"}), 400
    
    # Check room availability
    room_query = "SELECT * FROM rooms WHERE id = %s AND occupied < capacity"
    room = db.execute_query(room_query, (room_id,))
    
    if not room:
        return jsonify({"error": "Room is not available"}), 400
    
    # Create allocation
    allocation_query = """
        INSERT INTO allocations (student_id, room_id, allocated_date, status)
        VALUES (%s, %s, CURDATE(), 'Active')
    """
    allocation_id = db.execute_query(allocation_query, (student_id, room_id))
    
    # Update room occupancy
    update_query = "UPDATE rooms SET occupied = occupied + 1 WHERE id = %s"
    db.execute_query(update_query, (room_id,))
    
    # Update room status if full
    status_query = """
        UPDATE rooms 
        SET status = CASE 
            WHEN occupied >= capacity THEN 'Occupied'
            ELSE 'Available'
        END
        WHERE id = %s
    """
    db.execute_query(status_query, (room_id,))
    
    # Create fee record
    room_data = db.execute_query("SELECT rent FROM rooms WHERE id = %s", (room_id,))
    if room_data:
        fee_query = """
            INSERT INTO fees (student_id, amount, due_date, status)
            VALUES (%s, %s, DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'Pending')
        """
        db.execute_query(fee_query, (student_id, room_data[0]['rent']))
    
    return jsonify({
        "message": "Room allocated successfully",
        "allocation_id": allocation_id
    }), 201

# Fee Management
@app.route('/fees', methods=['GET'])
def get_fees():
    student_id = request.args.get('student_id')
    
    if student_id:
        query = """
            SELECT f.*, s.name, s.student_id
            FROM fees f
            JOIN students s ON f.student_id = s.id
            WHERE f.student_id = %s
            ORDER BY f.due_date DESC
        """
        fees = db.execute_query(query, (student_id,))
    else:
        query = """
            SELECT f.*, s.name, s.student_id
            FROM fees f
            JOIN students s ON f.student_id = s.id
            ORDER BY f.due_date DESC
        """
        fees = db.execute_query(query)
    
    return jsonify(fees)

@app.route('/fees/pay', methods=['POST'])
def pay_fee():
    data = request.json
    fee_id = data['fee_id']
    amount = data['amount']
    payment_mode = data.get('payment_mode', 'Cash')
    
    # Get fee details
    fee_query = "SELECT * FROM fees WHERE id = %s"
    fee = db.execute_query(fee_query, (fee_id,))
    
    if not fee:
        return jsonify({"error": "Fee record not found"}), 404
    
    fee = fee[0]
    
    # Update fee
    if amount >= fee['amount']:
        status = 'Paid'
        receipt_no = f"RCPT{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    else:
        status = 'Pending'
        receipt_no = None
    
    update_query = """
        UPDATE fees 
        SET paid_date = CURDATE(), 
            status = %s, 
            payment_mode = %s,
            receipt_no = %s
        WHERE id = %s
    """
    db.execute_query(update_query, (status, payment_mode, receipt_no, fee_id))
    
    return jsonify({
        "message": "Payment recorded successfully",
        "receipt_no": receipt_no,
        "status": status
    })

# Analytics
@app.route('/analytics/occupancy', methods=['GET'])
def get_occupancy_analytics():
    # Overall occupancy
    overall_query = """
        SELECT 
            COUNT(*) as total_rooms,
            SUM(capacity) as total_capacity,
            SUM(occupied) as total_occupied,
            ROUND((SUM(occupied) * 100.0 / SUM(capacity)), 2) as occupancy_rate
        FROM rooms
    """
    overall = db.execute_query(overall_query)
    
    # By block
    block_query = """
        SELECT 
            block,
            COUNT(*) as room_count,
            SUM(capacity) as total_capacity,
            SUM(occupied) as current_occupied,
            ROUND((SUM(occupied) * 100.0 / SUM(capacity)), 2) as occupancy_rate
        FROM rooms
        GROUP BY block
        ORDER BY block
    """
    by_block = db.execute_query(block_query)
    
    # Fee analytics
    fee_query = """
        SELECT 
            status,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM fees
        GROUP BY status
    """
    fee_stats = db.execute_query(fee_query)
    
    return jsonify({
        "overall": overall[0] if overall else {},
        "by_block": by_block,
        "fee_statistics": fee_stats
    })

@app.route('/analytics/financial', methods=['GET'])
def get_financial_analytics():
    # Monthly collection
    monthly_query = """
        SELECT 
            DATE_FORMAT(paid_date, '%Y-%m') as month,
            COUNT(*) as transactions,
            SUM(amount) as total_amount
        FROM fees
        WHERE status = 'Paid' AND paid_date IS NOT NULL
        GROUP BY DATE_FORMAT(paid_date, '%Y-%m')
        ORDER BY month DESC
        LIMIT 6
    """
    monthly = db.execute_query(monthly_query)
    
    # Pending fees
    pending_query = """
        SELECT 
            s.student_id,
            s.name,
            SUM(f.amount) as pending_amount,
            COUNT(f.id) as pending_count
        FROM students s
        JOIN fees f ON s.id = f.student_id
        WHERE f.status = 'Pending'
        GROUP BY s.id
        HAVING pending_amount > 0
    """
    pending = db.execute_query(pending_query)
    
    return jsonify({
        "monthly_collection": monthly,
        "pending_fees": pending
    })

# Search
@app.route('/search', methods=['GET'])
def search():
    query_param = request.args.get('q', '')
    if not query_param or len(query_param) < 2:
        return jsonify({"students": [], "rooms": []})
    
    search_term = f"%{query_param}%"
    
    # Search students
    student_query = """
        SELECT id, student_id, name, email, course
        FROM students
        WHERE student_id LIKE %s 
           OR name LIKE %s 
           OR email LIKE %s
        LIMIT 10
    """
    students = db.execute_query(student_query, (search_term, search_term, search_term))
    
    # Search rooms
    room_query = """
        SELECT id, room_no, block, floor, status, occupied, capacity
        FROM rooms
        WHERE room_no LIKE %s 
           OR block LIKE %s
        LIMIT 10
    """
    rooms = db.execute_query(room_query, (search_term, search_term))
    
    return jsonify({
        "students": students or [],
        "rooms": rooms or []
    })

# Inspections
@app.route('/inspections', methods=['GET'])
def get_inspections():
    inspection_query = """
        SELECT i.*, r.room_no, r.block
        FROM inspections i
        JOIN rooms r ON i.room_id = r.id
        ORDER BY i.inspection_date DESC
    """
    inspections = db.execute_query(inspection_query)
    return jsonify(inspections)

@app.route('/inspections', methods=['POST'])
def add_inspection():
    data = request.json
    query = """
        INSERT INTO inspections (room_id, inspection_date, inspector, rating, remarks)
        VALUES (%s, %s, %s, %s, %s)
    """
    inspection_id = db.execute_query(query, (
        data['room_id'], data['inspection_date'], 
        data['inspector'], data['rating'], data['remarks']
    ))
    
    return jsonify({
        "message": "Inspection recorded successfully",
        "inspection_id": inspection_id
    }), 201

if __name__ == '__main__':
    print("íº€ Starting Hostel Management System API...")
    print("í³Š API Documentation: http://localhost:5000")
    print("í²¾ Database: MySQL on localhost:3306")
    app.run(debug=True, port=5000)
