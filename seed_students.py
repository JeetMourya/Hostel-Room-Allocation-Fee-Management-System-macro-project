"""
seed_students.py
══════════════════════════════════════════════════════════════════════════════
Inserts 100 realistic college‑student records into hostel.db

What this script does
  1. Adds 40 extra rooms (Block C & D) so all 100 students can be housed
  2. Inserts 100 students (S005 – S104), each with:
       • A row in `students`                     (profile data)
       • A row in `users`                        (username + hashed password → can login)
       • A row in `student_verifications`        (pre‑approval code for self‑registration)
       • A row in `allocations`                  (room assignment)
       • A row in `fees`                         (current month fee, Pending)
  3. Skips any record whose student_id already exists (safe to re‑run)

Login convention for all 100 test students
  username : first‑name in lowercase, e.g. "aryan", "deepa"
  password : username + "123",        e.g. "aryan123"
  verify_code: "ADM" + student_id,   e.g. "ADMS005"

Run
  python seed_students.py
══════════════════════════════════════════════════════════════════════════════
"""

import sqlite3, hashlib, datetime, random, string, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hostel.db')

def h(p): return hashlib.sha256(p.encode()).hexdigest()
def rcpt(): return 'RCP' + datetime.datetime.now().strftime('%Y%m%d') + ''.join(random.choices(string.digits, k=4))

# ── 100 students data ──────────────────────────────────────────────────────────
# (student_id, name, email, phone, gender, dob, address, guardian_name, guardian_phone, course, year)
STUDENTS = [
    ('S005','Aryan Sharma','aryan@college.edu','9800000005','Male','2003-01-15','12 Rose Lane, Delhi','Ramesh Sharma','9700000005','B.Tech CSE',1),
    ('S006','Deepa Nair','deepa@college.edu','9800000006','Female','2003-03-22','34 Lotus St, Kerala','Suresh Nair','9700000006','B.Tech ECE',1),
    ('S007','Kabir Singh','kabir@college.edu','9800000007','Male','2002-07-08','56 Mango Rd, Punjab','Gurpreet Singh','9700000007','B.Tech ME',2),
    ('S008','Ananya Reddy','ananya@college.edu','9800000008','Female','2003-11-30','78 Peacock Ave, Hyderabad','Venkat Reddy','9700000008','MBA',1),
    ('S009','Vivek Patel','vivek@college.edu','9800000009','Male','2002-05-19','90 Jasmine Blvd, Surat','Haresh Patel','9700000009','BCA',2),
    ('S010','Meghna Iyer','meghna@college.edu','9800000010','Female','2004-02-14','11 Cloud St, Chennai','Rajan Iyer','9700000010','B.Sc CS',1),
    ('S011','Rohan Joshi','rohan@college.edu','9800000011','Male','2001-09-25','23 Sun Rd, Pune','Dinesh Joshi','9700000011','B.Tech CSE',3),
    ('S012','Simran Kaur','simran@college.edu','9800000012','Female','2003-06-10','45 Moon St, Amritsar','Harjit Kaur','9700000012','B.Tech ECE',1),
    ('S013','Aditya Verma','aditya@college.edu','9800000013','Male','2002-12-05','67 Star Lane, Lucknow','Sanjay Verma','9700000013','MBA',2),
    ('S014','Pooja Gupta','pooja@college.edu','9800000014','Female','2003-08-28','89 Park Ave, Jaipur','Rajiv Gupta','9700000014','BBA',1),
    ('S015','Nikhil Mehta','nikhil@college.edu','9800000015','Male','2001-04-17','101 Hill Rd, Ahmedabad','Sunil Mehta','9700000015','B.Tech ME',3),
    ('S016','Lakshmi Pillai','lakshmi@college.edu','9800000016','Female','2004-01-02','22 River St, Trivandrum','Mohan Pillai','9700000016','B.Sc CS',1),
    ('S017','Siddharth Ray','siddharth@college.edu','9800000017','Male','2002-10-20','44 Forest Rd, Kolkata','Bimal Ray','9700000017','B.Tech CSE',2),
    ('S018','Kavya Menon','kavya@college.edu','9800000018','Female','2003-07-15','66 Garden St, Kochi','Suresh Menon','9700000018','B.Tech ECE',1),
    ('S019','Harsh Agarwal','harsh@college.edu','9800000019','Male','2002-03-08','88 Market Rd, Kanpur','Anil Agarwal','9700000019','B.Tech CSE',2),
    ('S020','Tanya Mishra','tanya@college.edu','9800000020','Female','2003-09-22','110 Lake Ave, Bhopal','Rakesh Mishra','9700000020','MBA',1),
    ('S021','Gaurav Yadav','gaurav@college.edu','9800000021','Male','2001-11-11','13 Temple St, Varanasi','Ramji Yadav','9700000021','B.Tech ME',3),
    ('S022','Preethi Krishnan','preethi@college.edu','9800000022','Female','2004-05-28','35 Beach Rd, Coimbatore','Murali Krishnan','9700000022','BCA',1),
    ('S023','Yash Malhotra','yash@college.edu','9800000023','Male','2002-08-14','57 Hilltop Rd, Chandigarh','Vikram Malhotra','9700000023','BBA',2),
    ('S024','Snehal Desai','snehal@college.edu','9800000024','Female','2003-02-19','79 Cotton St, Nagpur','Rajesh Desai','9700000024','B.Sc CS',1),
    ('S025','Arjun Bose','arjun@college.edu','9800000025','Male','2001-06-30','91 Silk Rd, Kolkata','Subhash Bose','9700000025','B.Tech CSE',3),
    ('S026','Ishita Pandey','ishita@college.edu','9800000026','Female','2004-04-05','14 Spice Ave, Allahabad','Deepak Pandey','9700000026','B.Tech ECE',1),
    ('S027','Varun Nambiar','varun@college.edu','9800000027','Male','2002-12-22','36 Coconut St, Mangalore','Ravi Nambiar','9700000027','B.Tech ME',2),
    ('S028','Sakshi Saxena','sakshi.s@college.edu','9800000028','Female','2003-10-08','58 Rainbow Rd, Agra','Suresh Saxena','9700000028','MBA',1),
    ('S029','Kartik Bhatt','kartik@college.edu','9800000029','Male','2001-07-16','80 Snow Rd, Dehradun','Vijay Bhatt','9700000029','BBA',3),
    ('S030','Manisha Rao','manisha@college.edu','9800000030','Female','2004-03-24','102 Sunrise Blvd, Mysore','Gopal Rao','9700000030','B.Sc CS',1),
    ('S031','Devraj Choudhary','devraj@college.edu','9800000031','Male','2002-01-29','19 Desert Rd, Jodhpur','Bharat Choudhary','9700000031','B.Tech CSE',2),
    ('S032','Nidhi Sharma','nidhi@college.edu','9800000032','Female','2003-05-05','41 Golden St, Jaisalmer','Suresh Sharma','9700000032','B.Tech ECE',1),
    ('S033','Aman Tiwari','aman@college.edu','9800000033','Male','2001-02-18','63 Sacred Rd, Mathura','Ramesh Tiwari','9700000033','B.Tech ME',3),
    ('S034','Divya Pillai','divya.p@college.edu','9800000034','Female','2004-08-12','85 Sea Rd, Thiruvananthapuram','Suresh Pillai','9700000034','BCA',1),
    ('S035','Shreyas Kumar','shreyas@college.edu','9800000035','Male','2002-06-07','107 Valley Rd, Shimla','Rajesh Kumar','9700000035','BBA',2),
    ('S036','Anisha Singh','anisha@college.edu','9800000036','Female','2003-04-01','21 Ridge Road, Mussoorie','Ajay Singh','9700000036','B.Sc CS',1),
    ('S037','Parth Shah','parth@college.edu','9800000037','Male','2001-10-26','43 Diamond St, Surat','Nilesh Shah','9700000037','B.Tech CSE',3),
    ('S038','Megha Kulkarni','megha@college.edu','9800000038','Female','2004-07-19','65 Western Rd, Kolhapur','Dilip Kulkarni','9700000038','B.Tech ECE',1),
    ('S039','Rohit Das','rohit@college.edu','9800000039','Male','2002-09-04','87 Eastern Rd, Bhubaneswar','Nirmal Das','9700000039','B.Tech ME',2),
    ('S040','Shruti Jain','shruti@college.edu','9800000040','Female','2003-12-14','109 Northern Rd, Indore','Pramod Jain','9700000040','MBA',1),
    ('S041','Karan Trivedi','karan@college.edu','9800000041','Male','2001-03-23','24 Southern Ave, Vadodara','Harish Trivedi','9700000041','BBA',3),
    ('S042','Pallavi Deshpande','pallavi@college.edu','9800000042','Female','2004-06-08','46 Central St, Aurangabad','Hemant Deshpande','9700000042','B.Sc CS',1),
    ('S043','Saurabh Misra','saurabh@college.edu','9800000043','Male','2002-04-15','68 Trade Rd, Raipur','Sunil Misra','9700000043','B.Tech CSE',2),
    ('S044','Riya Chakraborty','riya@college.edu','9800000044','Female','2003-02-25','90 Art Blvd, Howrah','Sudip Chakraborty','9700000044','B.Tech ECE',1),
    ('S045','Akash Rawat','akash@college.edu','9800000045','Male','2001-08-31','12 Steel Rd, Bhilai','Govind Rawat','9700000045','B.Tech ME',3),
    ('S046','Tanvi Kapoor','tanvi@college.edu','9800000046','Female','2004-11-17','34 Fashion St, Ludhiana','Rajan Kapoor','9700000046','MBA',1),
    ('S047','Vishal Goel','vishal@college.edu','9800000047','Male','2002-02-06','56 Sports Rd, Patiala','Ashok Goel','9700000047','BBA',2),
    ('S048','Preeti Das','preeti@college.edu','9800000048','Female','2003-07-21','78 Green Rd, Guwahati','Ananda Das','9700000048','B.Sc CS',1),
    ('S049','Rahul Dixit','rahul.d@college.edu','9800000049','Male','2001-05-09','100 Mango Blvd, Gwalior','Dinesh Dixit','9700000049','B.Tech CSE',3),
    ('S050','Aishwarya Iyer','aishwarya@college.edu','9800000050','Female','2004-01-26','22 River Rd, Madurai','Krishnan Iyer','9700000050','B.Tech ECE',1),
    ('S051','Nitin Bhardwaj','nitin@college.edu','9800000051','Male','2002-11-13','44 Mountain Rd, Haridwar','Suresh Bhardwaj','9700000051','B.Tech ME',2),
    ('S052','Chandni Thakur','chandni@college.edu','9800000052','Female','2003-09-30','66 Temple Ave, Shirdi','Bhupesh Thakur','9700000052','MBA',1),
    ('S053','Sanjay Khanna','sanjay@college.edu','9800000053','Male','2001-06-19','88 Palace Rd, Jaipur','Deepak Khanna','9700000053','BBA',3),
    ('S054','Renu Vyas','renu@college.edu','9800000054','Female','2004-04-03','110 Museum St, Udaipur','Mahesh Vyas','9700000054','B.Sc CS',1),
    ('S055','Vikram Arora','vikram@college.edu','9800000055','Male','2002-08-28','15 Industrial Rd, Faridabad','Ramesh Arora','9700000055','B.Tech CSE',2),
    ('S056','Sudha Narayanan','sudha@college.edu','9800000056','Female','2003-03-15','37 Marina Rd, Chennai','Nair Narayanan','9700000056','B.Tech ECE',1),
    ('S057','Gaurav Chauhan','gaurav.c@college.edu','9800000057','Male','2001-01-04','59 Royal Rd, Jodhpur','Suresh Chauhan','9700000057','B.Tech ME',3),
    ('S058','Sunita Banerjee','sunita@college.edu','9800000058','Female','2004-10-21','81 Heritage Ave, Kolkata','Asim Banerjee','9700000058','MBA',1),
    ('S059','Aakash Soni','aakash@college.edu','9800000059','Male','2002-07-10','103 Lake St, Pushkar','Vijay Soni','9700000059','BBA',2),
    ('S060','Revathi Subramaniam','revathi@college.edu','9800000060','Female','2003-05-27','25 Old Town Rd, Coimbatore','Subramaniam G','9700000060','B.Sc CS',1),
    ('S061','Piyush Rastogi','piyush@college.edu','9800000061','Male','2001-12-16','47 New City Rd, Bareilly','Ramesh Rastogi','9700000061','B.Tech CSE',3),
    ('S062','Aparna Menon','aparna@college.edu','9800000062','Female','2004-06-01','69 Spice Garden Rd, Calicut','Rajesh Menon','9700000062','B.Tech ECE',1),
    ('S063','Harsh Lal','harsh.l@college.edu','9800000063','Male','2002-03-19','91 Crossing Rd, Meerut','Sunil Lal','9700000063','B.Tech ME',2),
    ('S064','Jyoti Dubey','jyoti@college.edu','9800000064','Female','2003-11-06','113 Camp Rd, Jhansi','Dinesh Dubey','9700000064','MBA',1),
    ('S065','Mohit Sethi','mohit@college.edu','9800000065','Male','2001-09-24','28 New Rd, Amritsar','Rakesh Sethi','9700000065','BBA',3),
    ('S066','Geeta Pillai','geeta@college.edu','9800000066','Female','2004-08-11','50 Arch Rd, Trivandrum','Gopalan Pillai','9700000066','B.Sc CS',1),
    ('S067','Tanmay Ghosh','tanmay@college.edu','9800000067','Male','2002-05-28','72 Port Rd, Haldia','Bikas Ghosh','9700000067','B.Tech CSE',2),
    ('S068','Mamta Agarwal','mamta@college.edu','9800000068','Female','2003-01-13','94 Silk St, Kanchipuram','Pramod Agarwal','9700000068','B.Tech ECE',1),
    ('S069','Rajat Bhatia','rajat@college.edu','9800000069','Male','2001-07-02','16 Tech Park Rd, Bengaluru','Suneel Bhatia','9700000069','B.Tech ME',3),
    ('S070','Kavita Srivastava','kavita@college.edu','9800000070','Female','2004-04-28','38 Smart City Rd, Pune','Ashok Srivastava','9700000070','MBA',1),
    ('S071','Kunal Pandya','kunal@college.edu','9800000071','Male','2002-10-15','60 Bay Rd, Veraval','Mukesh Pandya','9700000071','BBA',2),
    ('S072','Smita Rane','smita@college.edu','9800000072','Female','2003-06-30','82 Fort Rd, Aurangabad','Dilip Rane','9700000072','B.Sc CS',1),
    ('S073','Aniket Kulkarni','aniket@college.edu','9800000073','Male','2001-04-19','104 Signal Rd, Nasik','Suresh Kulkarni','9700000073','B.Tech CSE',3),
    ('S074','Sweta Ojha','sweta@college.edu','9800000074','Female','2004-02-05','26 Rail Nagar, Patna','Rajan Ojha','9700000074','B.Tech ECE',1),
    ('S075','Pranav Sahu','pranav@college.edu','9800000075','Male','2002-12-23','48 Grain Mkt, Raipur','Bharat Sahu','9700000075','B.Tech ME',2),
    ('S076','Deeksha Chand','deeksha@college.edu','9800000076','Female','2003-10-10','70 Civil Lines, Allahabad','Rajesh Chand','9700000076','MBA',1),
    ('S077','Anand Nair','anand@college.edu','9800000077','Male','2001-08-27','92 Boat Rd, Ernakulam','Suresh Nair','9700000077','BBA',3),
    ('S078','Namrata Bhosale','namrata@college.edu','9800000078','Female','2004-07-14','114 Fort Rd, Kolhapur','Dilip Bhosale','9700000078','B.Sc CS',1),
    ('S079','Sumit Naik','sumit@college.edu','9800000079','Male','2002-05-01','29 Beach Rd, Panjim','Sanjay Naik','9700000079','B.Tech CSE',2),
    ('S080','Heena Shaikh','heena@college.edu','9800000080','Female','2003-03-18','51 Old Market Rd, Aurangabad','Iqbal Shaikh','9700000080','B.Tech ECE',1),
    ('S081','Vikrant Tomar','vikrant@college.edu','9800000081','Male','2001-11-05','73 Border Rd, Agra','Rajpal Tomar','9700000081','B.Tech ME',3),
    ('S082','Sushma Reddy','sushma@college.edu','9800000082','Female','2004-09-22','95 MG Rd, Bengaluru','Venkat Reddy','9700000082','MBA',1),
    ('S083','Tarun Bansal','tarun@college.edu','9800000083','Male','2002-06-09','117 Ring Rd, New Delhi','Deepak Bansal','9700000083','BBA',2),
    ('S084','Archana Saini','archana@college.edu','9800000084','Female','2003-04-26','31 Town Hall Rd, Jaipur','Ramesh Saini','9700000084','B.Sc CS',1),
    ('S085','Vineet Ahuja','vineet@college.edu','9800000085','Male','2001-02-13','53 Lake View, Chandigarh','Suresh Ahuja','9700000085','B.Tech CSE',3),
    ('S086','Roshni Kapoor','roshni@college.edu','9800000086','Female','2004-12-30','75 Mall Rd, Shimla','Ashok Kapoor','9700000086','B.Tech ECE',1),
    ('S087','Sachin Thakkar','sachin@college.edu','9800000087','Male','2002-09-17','97 Park St, Ahmedabad','Bhavesh Thakkar','9700000087','B.Tech ME',2),
    ('S088','Poornima Vaidya','poornima@college.edu','9800000088','Female','2003-07-04','19 Green Park, Vadodara','Hemant Vaidya','9700000088','MBA',1),
    ('S089','Nikhil Garg','nikhil.g@college.edu','9800000089','Male','2001-05-22','41 White House, Meerut','Anil Garg','9700000089','BBA',3),
    ('S090','Disha Trivedi','disha@college.edu','9800000090','Female','2004-03-11','63 Blue Bell Rd, Baroda','Harish Trivedi','9700000090','B.Sc CS',1),
    ('S091','Rajesh Singhania','rajesh.s@college.edu','9800000091','Male','2002-01-28','85 Gold Street, Kolkata','Ramesh Singhania','9700000091','B.Tech CSE',2),
    ('S092','Madhuri Kale','madhuri@college.edu','9800000092','Female','2003-11-15','107 Silver Rd, Pune','Santosh Kale','9700000092','B.Tech ECE',1),
    ('S093','Samir Dubey','samir@college.edu','9800000093','Male','2001-09-02','22 Bronze Ave, Kanpur','Suresh Dubey','9700000093','B.Tech ME',3),
    ('S094','Bindu Thomas','bindu@college.edu','9800000094','Female','2004-06-20','44 Chapel Rd, Kottayam','Thomas K','9700000094','MBA',1),
    ('S095','Rushabh Jain','rushabh@college.edu','9800000095','Male','2002-04-07','66 Marble Rd, Rajkot','Pravin Jain','9700000095','BBA',2),
    ('S096','Lalitha Subramanian','lalitha@college.edu','9800000096','Female','2003-02-22','88 Statue Sq, Madurai','Subramaniam P','9700000096','B.Sc CS',1),
    ('S097','Deepak Sood','deepak@college.edu','9800000097','Male','2001-12-09','110 Freedom Rd, Ludhiana','Anil Sood','9700000097','B.Tech CSE',3),
    ('S098','Kamna Bajaj','kamna@college.edu','9800000098','Female','2004-10-27','25 Plaza Rd, Faridabad','Ramesh Bajaj','9700000098','B.Tech ECE',1),
    ('S099','Abhinav Mishra','abhinav@college.edu','9800000099','Male','2002-08-14','47 Cross Rd, Ghaziabad','Sanjay Mishra','9700000099','B.Tech ME',2),
    ('S100','Monica Pillai','monica@college.edu','9800000100','Female','2003-06-01','69 Library Rd, Ernakulam','Gopalan Nair','9700000100','MBA',1),
    ('S101','Shubham Agnihotri','shubham@college.edu','9800000101','Male','2001-03-20','91 Stadium Rd, Bhopal','Vikram Agnihotri','9700000101','BBA',3),
    ('S102','Surabhi Joshi','surabhi@college.edu','9800000102','Female','2004-01-08','113 Garden City, Bengaluru','Ashok Joshi','9700000102','B.Sc CS',1),
    ('S103','Aryan Malviya','aryan.m@college.edu','9800000103','Male','2002-11-25','27 Metro Rd, Lucknow','Vijay Malviya','9700000103','B.Tech CSE',2),
    ('S104','Bhavana Krishnamurthy','bhavana@college.edu','9800000104','Female','2003-09-12','49 Airport Rd, Hyderabad','Krishnamurthy R','9700000104','B.Tech ECE',1),
]

# ── Extra rooms ────────────────────────────────────────────────────────────────
# Block C (floor 1 & 2) and Block D (floor 1 & 2) — 40 rooms total
EXTRA_ROOMS = []
for block in ['C', 'D']:
    for floor in [1, 2]:
        for rno in range(1, 11):
            room_number = f"{floor}{rno:02d}" if block == 'C' else f"{floor}{rno+10:02d}"
            rtype = 'Single' if rno % 3 == 1 else ('Double' if rno % 3 == 2 else 'Triple')
            cap   = 1 if rtype == 'Single' else (2 if rtype == 'Double' else 3)
            rent  = 4200 if rtype == 'Single' else (3600 if rtype == 'Double' else 3000)
            dep   = rent + 500
            amen  = 'Fan, Cupboard' if floor == 1 else 'AC, Wi-Fi, Cupboard'
            full_rno = f"{block}{room_number}"
            EXTRA_ROOMS.append((full_rno, block, floor, rtype, cap, rent, dep, amen))

# ───────────────────────────────────────────────────────────────────────────────

def main():
    print(f"\n📂 Database: {DB_PATH}\n")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # ── 1. Add extra rooms ─────────────────────────────────────────────────────
    print("🏨 Ensuring extra rooms exist (Block C & D)...")
    rooms_added = 0
    for room in EXTRA_ROOMS:
        existing = c.execute("SELECT id FROM rooms WHERE room_no=?", (room[0],)).fetchone()
        if not existing:
            c.execute('''INSERT INTO rooms (room_no,block,floor,type,capacity,rent,deposit,amenities)
                         VALUES (?,?,?,?,?,?,?,?)''', room)
            rooms_added += 1
    print(f"   ✅ {rooms_added} new rooms added ({len(EXTRA_ROOMS) - rooms_added} already existed)\n")
    conn.commit()

    # ── 2. Get all available room IDs (block C & D) ────────────────────────────
    avail_rooms = c.execute(
        "SELECT id, capacity FROM rooms WHERE block IN ('C','D') AND occupied < capacity ORDER BY id"
    ).fetchall()
    room_pool = []
    for r in avail_rooms:
        for _ in range(r['capacity'] - c.execute(
            "SELECT COUNT(*) FROM allocations WHERE room_id=? AND status='Active'", (r['id'],)
        ).fetchone()[0]):
            room_pool.append(r['id'])

    print(f"   ℹ️  {len(room_pool)} available bed slots in Block C & D\n")

    # ── 3. Insert each student ─────────────────────────────────────────────────
    print("👨‍🎓 Inserting 100 students...\n")
    added = skipped = 0
    today = datetime.date.today().isoformat()
    month = datetime.date.today().strftime('%B %Y')
    due   = datetime.date.today().replace(day=10).isoformat()
    room_idx = 0

    for idx, stu in enumerate(STUDENTS):
        sid = stu[0]  # e.g. 'S005'
        name = stu[1]
        email = stu[2]
        username = name.split()[0].lower()  # first name lowercase

        # skip if student_id exists
        if c.execute("SELECT id FROM students WHERE student_id=?", (sid,)).fetchone():
            print(f"   ⏩ SKIP  {sid} — {name} (already in DB)")
            skipped += 1
            continue

        # ensure unique username (append number if taken)
        base_uname = username
        suffix = 2
        while c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
            username = f"{base_uname}{suffix}"
            suffix += 1

        password = username + '123'
        verify_code = 'ADM' + sid  # e.g. ADMS005

        # a) insert student
        try:
            c.execute('''INSERT INTO students
                (student_id,name,email,phone,gender,dob,address,guardian_name,guardian_phone,course,year)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)''', stu)
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  SKIP  {sid} — {name} (DB conflict: {e})")
            skipped += 1
            continue

        db_id = c.execute("SELECT id FROM students WHERE student_id=?", (sid,)).fetchone()['id']

        # b) user account
        c.execute("INSERT INTO users (username,password,role,student_id,name) VALUES (?,?,?,?,?)",
                  (username, h(password), 'student', db_id, name))

        # c) verification code (for self-registration demo)
        course = stu[9]; year = stu[10]; gender = stu[4]
        try:
            c.execute('''INSERT INTO student_verifications
                (verify_code,student_type,name,email,course,year,gender,is_registered,registered_at)
                VALUES (?,?,?,?,?,?,?,1,CURRENT_TIMESTAMP)''',
                (verify_code, 'fresher', name, email, course, year, gender))
        except Exception:
            pass  # already exists

        # d) room allocation
        if room_idx < len(room_pool):
            room_id = room_pool[room_idx]
            c.execute('''INSERT INTO allocations (student_id,room_id,allocated_date,status)
                         VALUES (?,?,?,'Active')''', (db_id, room_id, today))
            c.execute("UPDATE rooms SET occupied=occupied+1 WHERE id=?", (room_id,))
            c.execute("""UPDATE rooms SET status=CASE WHEN occupied>=capacity THEN 'Full' ELSE 'Available' END WHERE id=?""",
                      (room_id,))
            room_idx += 1

        # e) fee record
        rent = c.execute("SELECT r.rent FROM allocations a JOIN rooms r ON r.id=a.room_id WHERE a.student_id=? AND a.status='Active'", (db_id,)).fetchone()
        fee_amount = rent['rent'] if rent else 4000
        receipt = rcpt()
        fee_status = random.choice(['Paid', 'Paid', 'Pending'])  # 2:1 ratio paid
        paid_date = today if fee_status == 'Paid' else None
        c.execute('''INSERT INTO fees (student_id,month,amount,due_date,paid_date,status,receipt_no)
                     VALUES (?,?,?,?,?,?,?)''',
                  (db_id, month, fee_amount, due, paid_date, fee_status, receipt))

        conn.commit()
        print(f"   ✅ {sid}  {name:<30} user={username:<15} pass={password}")
        added += 1

    conn.close()

    print(f"\n{'═'*60}")
    print(f"✅ Done!   Added: {added}   |   Skipped (already existed): {skipped}")
    print(f"{'═'*60}")
    print(f"""
🎯 HOW TO TEST STUDENT LOGIN
────────────────────────────────────────────────────────────
Username pattern : first name (lowercase), e.g.  aryan
Password pattern : username + 123,         e.g.  aryan123

Quick reference (first 10):
  S005  aryan / aryan123        → Aryan Sharma
  S006  deepa / deepa123        → Deepa Nair
  S007  kabir / kabir123        → Kabir Singh
  S008  ananya / ananya123      → Ananya Reddy
  S009  vivek / vivek123        → Vivek Patel
  S010  meghna / meghna123      → Meghna Iyer
  S011  rohan / rohan123        → Rohan Joshi
  S012  simran / simran123      → Simran Kaur
  S013  aditya / aditya123      → Aditya Verma
  S014  pooja / pooja123        → Pooja Gupta

Admin access:   admin / admin123   (full access)
Warden access:  warden / warden123 (full access)
────────────────────────────────────────────────────────────
""")

if __name__ == '__main__':
    main()
