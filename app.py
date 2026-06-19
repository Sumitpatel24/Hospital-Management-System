from flask import Flask, render_template, request, redirect
import mysql.connector
import pandas as pd
from flask import send_file
from flask import flash
from datetime import datetime
from reportlab.pdfgen import canvas
from flask import jsonify
app = Flask(__name__)
app.secret_key = "hospital123"
from flask import session, flash

# MySQL Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sumitpatel05",
    database="hospital_db"
)

cursor = conn.cursor(buffered=True)

@app.route('/')
def home():

    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]

    return render_template(
        'index.html',
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments
    )

@app.route('/patient_register', methods=['GET', 'POST'])
def patient_register():

    if request.method == 'POST':

        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        disease = request.form['disease']
        password = request.form['password']

        if len(password) < 6:
            flash("Password must be minimum 6 characters")
            return redirect('/patient_register')

        if " " in password:
            flash("Spaces are not allowed in password")
            return redirect('/patient_register')

        # Check Phone Already Exists

        cursor.execute("""
        SELECT *
        FROM patients
        WHERE phone=%s
        """, (phone,))

        existing_patient = cursor.fetchone()

        if existing_patient:
            return "Mobile Number Already Registered"

        # Insert New Patient

        cursor.execute("""
        INSERT INTO patients
        (
            name,
            age,
            gender,
            phone,
            disease,
            password
        )
        VALUES
        (%s,%s,%s,%s,%s,%s)
        """,
        (
            name,
            age,
            gender,
            phone,
            disease,
            password
        ))

        conn.commit()

        return redirect('/patient_login')

    return render_template('patient_register.html')

@app.route('/patient_login', methods=['GET', 'POST'])
def patient_login():

    if request.method == 'POST':

        phone = request.form['phone']
        password = request.form['password']

        cursor.execute("""
        SELECT *
        FROM patients
        WHERE phone=%s
        """, (phone,))

        patient = cursor.fetchone()

        if patient:

            if str(patient[6]) == str(password):

                # Remove all old sessions
                session.clear()

                # Create patient session
                session['patient_phone'] = phone

                return redirect('/patient_dashboard')

        flash("❌ Invalid Mobile Number or Password")

        return redirect('/patient_login')

    return render_template('patient_login.html')

@app.route('/patient_profile')
def patient_profile():

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    phone = session['patient_phone']

    cursor.execute("""
    SELECT *
    FROM patients
    WHERE phone=%s
    """,(phone,))

    patient = cursor.fetchone()

    cursor.execute("""
    SELECT *
    FROM appointments
    WHERE patient_phone=%s
    ORDER BY appointment_date DESC
    """,(phone,))

    appointments = cursor.fetchall()

    return render_template(
        'patient_profile.html',
        patient=patient,
        appointments=appointments
    )

@app.route('/edit_patient_profile',
           methods=['GET','POST'])
def edit_patient_profile():

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    phone = session['patient_phone']

    if request.method == 'POST':

        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        disease = request.form['disease']

        cursor.execute("""
        UPDATE patients
        SET name=%s,
            age=%s,
            gender=%s,
            disease=%s
        WHERE phone=%s
        """,
        (name, age, gender, disease, phone))

        conn.commit()

        return redirect('/patient_profile')

    cursor.execute("""
    SELECT *
    FROM patients
    WHERE phone=%s
    """,(phone,))

    patient = cursor.fetchone()

    return render_template(
        'edit_patient_profile.html',
        patient=patient
    )

@app.route('/patient_change_password', methods=['GET', 'POST'])
def patient_change_password():

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    if request.method == 'POST':

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        cursor.execute("""
        SELECT password
        FROM patients
        WHERE phone=%s
        """,(session['patient_phone'],))

        result = cursor.fetchone()

        if not result:
            return "Patient Not Found"

        old_password = result[0]

        if current_password != old_password:
            flash("❌ Current Password Wrong")
            return redirect('/change_password')

        if new_password != confirm_password:
            flash("❌ Passwords Do Not Match")
            return redirect('/change_password')

        if len(new_password) < 6:
            flash("❌ Password Must Be At Least 6 Characters")
            return redirect('/change_password')

        cursor.execute("""
        UPDATE patients
        SET password=%s
        WHERE phone=%s
        """,
        (
            new_password,
            session['patient_phone']
        ))

        conn.commit()

        flash("✅ Password Changed Successfully")
        
        return redirect('/patient_dashboard')

    return render_template('patient_change_password.html')

@app.route('/forgot_password',
           methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        phone = request.form['phone']
        age = int(request.form['age'])
        new_password = request.form['new_password']

        # Password Validation

        if len(new_password) < 6:

            flash("❌ Password must be minimum 6 characters")

            return redirect('/forgot_password')

        if " " in new_password:

            flash("❌ Spaces are not allowed in password")

            return redirect('/forgot_password')

        # Verify Patient

        cursor.execute("""
        SELECT *
        FROM patients
        WHERE phone=%s
        AND age=%s
        """,
        (
            phone,
            age
        ))

        patient = cursor.fetchone()

        if patient:

            cursor.execute("""
            UPDATE patients
            SET password=%s
            WHERE phone=%s
            """,
            (
                new_password,
                phone
            ))

            conn.commit()

            flash("✅ Password Updated Successfully")

            return redirect('/patient_login')

        else:

            flash("❌ Mobile Number or Age Incorrect")

            return redirect('/forgot_password')

    return render_template(
        'forgot_password.html'
    )

@app.route('/patient_dashboard')
def patient_dashboard():

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    phone = session['patient_phone']

    cursor.execute("""
    SELECT *
    FROM patients
    WHERE phone=%s
    """,(phone,))

    patient = cursor.fetchone()

    # Appointments

    cursor.execute("""
    SELECT *
    FROM appointments
    WHERE patient_phone=%s
    ORDER BY id DESC
    LIMIT 5
    """,(phone,))

    appointments = cursor.fetchall()

    cursor.execute("""
    SELECT COUNT(*)
    FROM appointments
    WHERE patient_phone=%s
    """,(phone,))

    total_appointments = cursor.fetchone()[0]

    # Prescriptions

    cursor.execute("""
    SELECT *
    FROM prescriptions
    WHERE patient_name=%s
    ORDER BY id DESC
    LIMIT 5
    """,(patient[1],))

    prescriptions = cursor.fetchall()

    cursor.execute("""
    SELECT COUNT(*)
    FROM prescriptions
    WHERE patient_name=%s
    """,(patient[1],))

    total_prescriptions = cursor.fetchone()[0]

    # Bills

    cursor.execute("""
    SELECT *
    FROM bills
    WHERE phone_number=%s
    ORDER BY id DESC
    LIMIT 5
    """,(phone,))

    bills = cursor.fetchall()

    cursor.execute("""
    SELECT COUNT(*)
    FROM bills
    WHERE phone_number=%s
    """,(phone,))

    total_bills = cursor.fetchone()[0]

    return render_template(
        'patient_dashboard.html',
        patient=patient,
        appointments=appointments,
        prescriptions=prescriptions,
        bills=bills,
        total_appointments=total_appointments,
        total_prescriptions=total_prescriptions,
        total_bills=total_bills
    )

@app.route('/my_appointments')
def my_appointments():

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    phone = session['patient_phone']

    cursor.execute("""
    SELECT *
    FROM appointments
    WHERE patient_phone=%s
    ORDER BY appointment_date DESC
    """,(phone,))

    appointments = cursor.fetchall()

    return render_template(
        'my_appointments.html',
        appointments=appointments
    )

@app.route('/my_prescriptions')
def my_prescriptions():

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    phone = session['patient_phone']

    cursor.execute("""
    SELECT *
    FROM patients
    WHERE phone=%s
    """,(phone,))

    patient = cursor.fetchone()

    if not patient:
        return redirect('/patient_login')

    patient_name = patient[1]

    cursor.execute("""
    SELECT *
    FROM prescriptions
    WHERE patient_name=%s
    ORDER BY id DESC
    """,(patient_name,))

    prescriptions = cursor.fetchall()

    return render_template(
        'my_prescriptions.html',
        prescriptions=prescriptions
    )

@app.route('/my_bills')
def my_bills():

    if 'patient_phone' not in session:
        return redirect('/patient_login')

    phone = session['patient_phone']

    cursor.execute("""
    SELECT *
    FROM patients
    WHERE phone=%s
    """,(phone,))

    patient = cursor.fetchone()

    if not patient:
        return redirect('/patient_login')

    patient_name = patient[1]

    cursor.execute("""
    SELECT *
    FROM bills
    WHERE patient_name=%s
    ORDER BY id DESC
    """,(patient_name,))

    bills = cursor.fetchall()

    return render_template(
        'my_bills.html',
        bills=bills
    )  

@app.route('/patient_logout')
def patient_logout():

    session.pop('patient_phone', None)

    return redirect('/')

    return redirect('/patient_login')

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cursor.fetchone()

        if user:

          session.clear()

          session['admin'] = email

        return redirect('/dashboard')

        flash("Invalid Email or Password ❌")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():

    if 'admin' not in session:
        return redirect('/login')

    if 'admin' not in session:
        return redirect('/login')

    # Dashboard Counts

    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM prescriptions")
    total_prescriptions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bills")
    total_bills = cursor.fetchone()[0]

    # Appointment Status

    cursor.execute("""
    SELECT COUNT(*)
    FROM appointments
    WHERE status='Waiting'
    """)
    waiting = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM appointments
    WHERE status='Completed'
    """)
    completed = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM appointments
    WHERE status='Cancelled'
    """)
    cancelled = cursor.fetchone()[0]

    # Today's Appointments

    cursor.execute("""
    SELECT COUNT(*)
    FROM appointments
    WHERE appointment_date = CURDATE()
    """)
    today_appointments = cursor.fetchone()[0]

    # Most Busy Doctor

    cursor.execute("""
    SELECT doctor_name,
           COUNT(*) AS total
    FROM appointments
    GROUP BY doctor_name
    ORDER BY total DESC
    LIMIT 1
    """)
    busy_doctor = cursor.fetchone()

    # Most Common Disease

    cursor.execute("""
    SELECT problem,
           COUNT(*) AS total
    FROM appointments
    GROUP BY problem
    ORDER BY total DESC
    LIMIT 1
    """)
    common_disease = cursor.fetchone()

    # Best Doctor

    cursor.execute("""
    SELECT name, rating
    FROM doctors
    ORDER BY rating DESC
    LIMIT 1
    """)
    best_doctor = cursor.fetchone()

    # Revenue

    cursor.execute("""
    SELECT SUM(total_amount)
    FROM bills
    """)
    total_revenue = cursor.fetchone()[0] or 0

    cursor.execute("""
    SELECT SUM(total_amount)
    FROM bills
    WHERE DATE(bill_date)=CURDATE()
    """)
    today_revenue = cursor.fetchone()[0] or 0

    cursor.execute("""
    SELECT SUM(total_amount)
    FROM bills
    WHERE MONTH(bill_date)=MONTH(CURDATE())
    AND YEAR(bill_date)=YEAR(CURDATE())
    """)
    month_revenue = cursor.fetchone()[0] or 0

    # Recent Patients

    cursor.execute("""
    SELECT *
    FROM patients
    ORDER BY id DESC
    LIMIT 5
    """)
    recent_patients = cursor.fetchall()

    # Recent Doctors

    cursor.execute("""
    SELECT *
    FROM doctors
    ORDER BY id DESC
    LIMIT 5
    """)
    recent_doctors = cursor.fetchall()

    # Recent Appointments

    cursor.execute("""
    SELECT *
    FROM appointments
    ORDER BY appointment_date DESC,
             token_no ASC
    LIMIT 5
    """)
    recent_appointments = cursor.fetchall()

    # Recent Bills

    cursor.execute("""
    SELECT *
    FROM bills
    ORDER BY id DESC
    LIMIT 5
    """)
    recent_bills = cursor.fetchall()

    return render_template(
        'dashboard.html',

        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        total_prescriptions=total_prescriptions,
        total_bills=total_bills,

        waiting=waiting,
        completed=completed,
        cancelled=cancelled,

        today_appointments=today_appointments,

        busy_doctor=busy_doctor,
        common_disease=common_disease,
        best_doctor=best_doctor,

        total_revenue=total_revenue,
        today_revenue=today_revenue,
        month_revenue=month_revenue,

        recent_patients=recent_patients,
        recent_doctors=recent_doctors,
        recent_appointments=recent_appointments,
        recent_bills=recent_bills
    )    

@app.route('/prescriptions', methods=['GET', 'POST'])
def prescriptions():

    if request.method == 'POST':

        try:

            patient_name = request.form.get('patient_name')
            doctor_name = request.form.get('doctor_name')
            disease = request.form.get('disease')
            medicines = request.form.get('medicines')
            advice = request.form.get('advice')

            cursor.execute("""
                INSERT INTO prescriptions
                (
                    patient_name,
                    doctor_name,
                    disease,
                    medicines,
                    advice,
                    prescription_date
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW()
                )
            """,
            (
                patient_name,
                doctor_name,
                disease,
                medicines,
                advice
            ))

            conn.commit()

            flash("Prescription Saved Successfully ✅")

        except Exception as e:

            conn.rollback()

            print("ERROR :", e)

            flash(f"Error: {e}")

    search = request.args.get('search', '')

    if search:

        cursor.execute("""
            SELECT *
            FROM prescriptions
            WHERE patient_name LIKE %s
            OR doctor_name LIKE %s
            OR disease LIKE %s
            ORDER BY id DESC
        """,
        (
            '%' + search + '%',
            '%' + search + '%',
            '%' + search + '%'
        ))

    else:

        cursor.execute("""
            SELECT *
            FROM prescriptions
            ORDER BY id DESC
        """)

    data = cursor.fetchall()

    return render_template(
        'prescriptions.html',
        prescriptions=data
    )


@app.route('/print_prescription/<int:id>')
def print_prescription(id):

    cursor.execute(
        "SELECT * FROM prescriptions WHERE id=%s",
        (id,)
    )

    prescription = cursor.fetchone()

    return render_template(
        'print_prescription.html',
        prescription=prescription
    )

@app.route('/delete_prescription/<int:id>')
def delete_prescription(id):

    cursor.execute(
        "DELETE FROM prescriptions WHERE id=%s",
        (id,)
    )

    conn.commit()

    flash("Prescription Deleted Successfully ✅")

    return redirect('/prescriptions')

@app.route('/edit_prescription/<int:id>',
methods=['GET','POST'])
def edit_prescription(id):

    if request.method == 'POST':

        medicines = request.form['medicines']
        advice = request.form['advice']

        cursor.execute("""
        UPDATE prescriptions
        SET medicines=%s,
            advice=%s
        WHERE id=%s
        """,
        (medicines, advice, id))

        conn.commit()

        flash("Prescription Updated Successfully ✅")

        return redirect('/prescriptions')

    cursor.execute(
        "SELECT * FROM prescriptions WHERE id=%s",
        (id,)
    )

    prescription = cursor.fetchone()

    return render_template(
        'edit_prescription.html',
        prescription=prescription
    )

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():

    if 'admin' not in session:
        return redirect('/login')

    if request.method == 'POST':

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        cursor.execute(
            """
            SELECT password
            FROM admin
            WHERE username=%s
            """,
            (session['admin'],)
        )

        result = cursor.fetchone()

        if not result:
            return "Admin Not Found"

        old_password = result[0]

        if current_password != old_password:
            flash("❌ Current Password Wrong")
            return redirect('/change_password')

        if new_password != confirm_password:
            flash("❌ Passwords Do Not Match")
            return redirect('/change_password')

        if len(new_password) < 6:
            flash("❌ Password Must Be At Least 6 Characters")
            return redirect('/change_password')

        cursor.execute(
            """
            UPDATE admin
            SET password=%s
            WHERE username=%s
            """,
            (
                new_password,
                session['admin']
            )
        )

        conn.commit()

        flash("✅ Password Changed Successfully")
        
        return redirect('/dashboard')

    return render_template('change_password.html')

@app.route('/logout')
def logout():

    session.pop('admin', None)

    return redirect('/')

@app.route('/register_patient', methods=['GET', 'POST'])
def register_patient():

    if request.method == 'POST':

        name = request.form['name']
        gender = request.form['gender']
        phone = request.form['phone']
        disease = request.form['disease']
        age = request.form['age']

        # Age Validation

        if not age.isdigit():
            flash("Age must contain only numbers ❌")
            return redirect('/register_patient')

        age = int(age)

        if age < 0 or age > 120:
            flash("Age must be between 0 and 120 ❌")
            return redirect('/register_patient')

        # Phone Validation

        if len(phone) != 10:
            flash("Phone number must be exactly 10 digits ❌")
            return redirect('/register_patient')

        if not phone.isdigit():
            flash("Phone number must contain only digits ❌")
            return redirect('/register_patient')

        # Duplicate Phone Check

        cursor.execute(
            "SELECT * FROM patients WHERE phone=%s",
            (phone,)
        )

        check = cursor.fetchone()

        if check:
            flash("Patient with this phone number already exists ❌")
            return redirect('/register_patient')

        # Insert Patient

        sql = """
        INSERT INTO patients
        (
            name,
            age,
            gender,
            phone,
            disease
        )
        VALUES (%s,%s,%s,%s,%s)
        """

        values = (
            name,
            age,
            gender,
            phone,
            disease
        )

        cursor.execute(sql, values)
        conn.commit()

        flash("Patient Registered Successfully ✅")

        return redirect('/register_patient')

    return render_template('register_patient.html')

@app.route('/patients')
def patients():

    search = request.args.get('search', '')

    sql = """
    SELECT *
    FROM patients
    WHERE name LIKE %s
       OR phone LIKE %s
    ORDER BY id DESC
    """

    value = "%" + search + "%"

    cursor.execute(sql, (value, value))

    data = cursor.fetchall()
    
    return render_template(
        'patients.html',
        patients=data,
        search=search
    )

@app.route('/patient/<int:id>')
def view_patient(id):

    cursor.execute(
        "SELECT * FROM patients WHERE id=%s",
        (id,)
    )

    patient = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM appointments
        WHERE patient_name=%s
        ORDER BY appointment_date DESC
    """,(patient[1],))

    appointments = cursor.fetchall()

    print("PATIENT =", patient)
    print("APPOINTMENTS =", appointments)

    return render_template(
        'patient_profile.html',
        patient=patient,
        appointments=appointments
    )

@app.route('/delete_patient/<int:id>')
def delete_patient(id):

    cursor.execute(
        "DELETE FROM patients WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect('/patients')

@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):

    if request.method == 'POST':

        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        disease = request.form['disease']

        cursor.execute("""
        UPDATE patients
        SET name=%s,
            age=%s,
            gender=%s,
            phone=%s,
            disease=%s
        WHERE id=%s
        """,
        (name, age, gender, phone, disease, id))

        conn.commit()

        flash("Patient Updated Successfully ✅")

        return redirect('/patients')

    cursor.execute(
        "SELECT * FROM patients WHERE id=%s",
        (id,)
    )

    patient = cursor.fetchone()

    return render_template(
        'edit_patient.html',
        patient=patient
    )

@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():

    if request.method == 'POST':

        name = request.form['name']
        specialization = request.form['specialization']
        degree = request.form['degree']
        experience = request.form['experience']
        rating = request.form['rating']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']

        # Password Validation

        if len(password) < 6:
            return """
            <h2>Password must be at least 6 characters</h2>
            <a href='/add_doctor'>Go Back</a>
            """

        # Phone Validation

        if not phone.isdigit():
            return """
            <h2>Phone must contain only digits</h2>
            <a href='/add_doctor'>Go Back</a>
            """

        if len(phone) != 10:
            return """
            <h2>Phone number must be exactly 10 digits</h2>
            <a href='/add_doctor'>Go Back</a>
            """

        if phone[0] not in "6789":
            return """
            <h2>Phone number must start with 6, 7, 8 or 9</h2>
            <a href='/add_doctor'>Go Back</a>
            """

        # Duplicate Phone Check

        cursor.execute(
            "SELECT * FROM doctors WHERE phone=%s",
            (phone,)
        )

        existing_phone = cursor.fetchone()

        if existing_phone:
            return """
            <h2>Phone Number Already Exists</h2>
            <a href='/add_doctor'>Go Back</a>
            """

        # Duplicate Email Check

        cursor.execute(
            "SELECT * FROM doctors WHERE email=%s",
            (email,)
        )

        existing_email = cursor.fetchone()

        if existing_email:
            return """
            <h2>Email Already Exists</h2>
            <a href='/add_doctor'>Go Back</a>
            """

        # Insert Doctor

        sql = """
        INSERT INTO doctors
        (
            name,
            specialization,
            degree,
            experience,
            rating,
            phone,
            email,
            password
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            name,
            specialization,
            degree,
            int(experience),
            float(rating),
            phone,
            email,
            password
        )

        cursor.execute(sql, values)
        conn.commit()

        flash("Doctor Added Successfully ✅")

        return redirect('/add_doctor')

    return render_template('add_doctor.html')
    
@app.route('/doctors')
def doctors():

    search = request.args.get('search')

    if search:

        cursor.execute("""
            SELECT *
            FROM doctors
            WHERE name LIKE %s
            OR specialization LIKE %s
        """,
        (
            '%' + search + '%',
            '%' + search + '%'
        ))

    else:

        cursor.execute(
            "SELECT * FROM doctors"
        )

    data = cursor.fetchall()

    return render_template(
        'doctors.html',
        doctors=data
    )

@app.route('/doctor/<int:id>')
def doctor_profile(id):

    cursor.execute(
        "SELECT * FROM doctors WHERE id=%s",
        (id,)
    )

    doctor = cursor.fetchone()

    return render_template(
        'doctor_profile.html',
        doctor=doctor
    )

@app.route('/delete_doctor/<int:id>')
def delete_doctor(id):

    cursor.execute(
        "DELETE FROM doctors WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect('/doctors')

@app.route('/edit_doctor/<int:id>', methods=['GET', 'POST'])
def edit_doctor(id):

    if request.method == 'POST':

        name = request.form['name']
        specialization = request.form['specialization']

        if specialization == "":
         return "Please Select Specialization"
        
        degree = request.form['degree']
        experience = request.form['experience']
        rating = request.form['rating']
        phone = request.form['phone']
        email = request.form['email']

        sql = """
        UPDATE doctors
        SET name=%s,
            specialization=%s,
            degree=%s,
            experience=%s,
            rating=%s,
            phone=%s,
            email=%s
        WHERE id=%s
        """

        cursor.execute(
            sql,
            (
                name,
                specialization,
                degree,
                experience,
                rating,
                phone,
                email,
                id
            )
        )

        conn.commit()

        return redirect('/doctors')

    cursor.execute(
        "SELECT * FROM doctors WHERE id=%s",
        (id,)
    )

    doctor = cursor.fetchone()

    return render_template(
        'edit_doctor.html',
        doctor=doctor
    )

@app.route('/doctor_login', methods=['GET','POST'])
def doctor_login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor.execute("""
        SELECT *
        FROM doctors
        WHERE email=%s AND password=%s
        """,(email,password))

        doctor = cursor.fetchone()

        if doctor:

            session.clear()

            session['doctor_email'] = email
            session['doctor_name'] = doctor[1]

            return redirect('/doctor_dashboard')

        return "Invalid Email or Password"

    return render_template('doctor_login.html')

@app.route('/doctor_dashboard')
def doctor_dashboard():

    if 'doctor_email' not in session:
        return redirect('/doctor_login')

    if 'doctor_email' not in session:
        return redirect('/doctor_login')

    doctor_name = session['doctor_name']

    # Waiting patients pehle, fir date wise, fir token wise
    cursor.execute("""
    SELECT *
    FROM appointments
    WHERE doctor_name=%s
    ORDER BY
        CASE
            WHEN status='Waiting' THEN 1
            WHEN status='Completed' THEN 2
            ELSE 3
        END,
        appointment_date ASC,
        token_no ASC
    """, (doctor_name,))

    appointments = cursor.fetchall()

    cursor.execute("""
    SELECT *
    FROM doctors
    WHERE email=%s
    """, (session['doctor_email'],))

    doctor = cursor.fetchone()

    total_appointments = len(appointments)

    return render_template(
        'doctor_dashboard.html',
        doctor=doctor,
        doctor_name=doctor_name,
        appointments=appointments,
        total_appointments=total_appointments
    )

@app.route('/doctor_change_password', methods=['GET', 'POST'])
def doctor_change_password():

    if 'doctor_email' not in session:
        return redirect('/doctor_login')

    if request.method == 'POST':

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        cursor.execute("""
        SELECT password
        FROM doctors
        WHERE email=%s
        """,(session['doctor_email'],))

        result = cursor.fetchone()

        if not result:
            return "Doctor Not Found"

        old_password = result[0]

        if current_password != old_password:
            flash("❌ Current Password Wrong")
            return redirect('/change_password')


        if new_password != confirm_password:
            flash("❌ Passwords Do Not Match")
            return redirect('/change_password')

        if len(new_password) < 6:
            flash("❌ Password Must Be At Least 6 Characters")
            return redirect('/change_password')

        cursor.execute("""
        UPDATE doctors
        SET password=%s
        WHERE email=%s
        """,
        (
            new_password,
            session['doctor_email']
        ))

        flash("✅ Password Changed Successfully")
        
        return redirect('/doctor_dashboard')


    return render_template('doctor_change_password.html')

@app.route('/add_prescription/<int:appointment_id>',
           methods=['GET','POST'])
def add_prescription(appointment_id):

    cursor.execute("""
    SELECT *
    FROM appointments
    WHERE id=%s
    """,(appointment_id,))

    appointment = cursor.fetchone()

    if request.method == 'POST':

        medicines = request.form['medicines']
        advice = request.form['advice']

        cursor.execute("""
        INSERT INTO prescriptions
        (
            patient_name,
            doctor_name,
            disease,
            medicines,
            advice,
            prescription_date,
            phone_number
        )
        VALUES
        (%s,%s,%s,%s,%s,NOW(),%s)
        """,
        (
            appointment[1],
            appointment[2],
            appointment[3],
            medicines,
            advice,
            appointment[8]
        ))

        cursor.execute("""
            UPDATE appointments
            SET status='Completed'
            WHERE id=%s
            """,(appointment_id,))

        conn.commit()

        return redirect('/doctor_dashboard')

    return render_template(
        'doctor_prescription.html',
        appointment=appointment
    )

@app.route('/doctor_logout')
def doctor_logout():

    session.pop('doctor_email', None)
    session.pop('doctor_name', None)

    return redirect('/')

@app.route('/add_appointment', methods=['GET', 'POST'])
def add_appointment():

    # Admin ya Patient login hona chahiye
    if 'admin' not in session and 'patient_phone' not in session:
        return redirect('/')

    if request.method == 'POST':

        phone = request.form['phone']
        patient_name = request.form['patient_name']
        doctor_name = request.form['doctor_name']
        problem = request.form['problem']
        appointment_date = request.form['appointment_date']

        if problem == "Other":
            problem = request.form['other_problem']

        # Generate Token Number

        cursor.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE doctor_name=%s
        AND appointment_date=%s
        """, (doctor_name, appointment_date))

        token_no = cursor.fetchone()[0] + 1

        # Insert Appointment

        cursor.execute("""
        INSERT INTO appointments
        (
            patient_name,
            doctor_name,
            problem,
            appointment_date,
            token_no,
            status,
            patient_phone
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            patient_name,
            doctor_name,
            problem,
            appointment_date,
            token_no,
            'Waiting',
            phone
        ))

        conn.commit()

        print("ADMIN =", session.get('admin'))
        print("PATIENT =", session.get('patient_phone'))

        # User Type Check

        if 'admin' in session:
            user_type = "admin"
        else:
            user_type = "patient"

        return render_template(
            'appointment_success.html',
            patient_name=patient_name,
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            token_no=token_no,
            user_type=user_type
        )

    # GET Request

    cursor.execute("""
    SELECT *
    FROM doctors
    ORDER BY name
    """)
    doctors = cursor.fetchall()

    cursor.execute("""
    SELECT *
    FROM patients
    ORDER BY name
    """)
    patients = cursor.fetchall()

    return render_template(
        'add_appointment.html',
        doctors=doctors,
        patients=patients
    )

@app.route('/appointments')
def appointments():

    search = request.args.get('search', '')
    status = request.args.get('status', '')

    sql = """
    SELECT *
    FROM appointments
    WHERE 1=1
    """

    values = []

    if search:
        sql += """
        AND (
            patient_name LIKE %s
            OR doctor_name LIKE %s
        )
        """
        values.append('%' + search + '%')
        values.append('%' + search + '%')

    if status:
        sql += " AND status=%s "
        values.append(status)

    sql += """
         ORDER BY appointment_date DESC,
         id DESC
         """

    cursor.execute(sql, tuple(values))

    data = cursor.fetchall()

    return render_template(
        'appointments.html',
        appointments=data
    )

@app.route('/complete_appointment/<int:id>')
def complete_appointment(id):

    cursor.execute(
        "UPDATE appointments SET status='Completed' WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect('/appointments')

@app.route('/cancel_appointment/<int:id>')
def cancel_appointment(id):

    cursor.execute(
        "UPDATE appointments SET status='Cancelled' WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect('/appointments')

@app.route('/delete_appointment/<int:id>')
def delete_appointment(id):

    cursor.execute(
        "DELETE FROM appointments WHERE id=%s",
        (id,)
    )

    conn.commit()

    flash("Appointment Deleted Successfully")

    return redirect('/appointments')

@app.route('/get_patient/<phone>')
def get_patient(phone):

    cursor.execute("""
    SELECT p.name,
           p.age,
           p.gender,
           a.doctor_name,
           a.problem
    FROM patients p
    LEFT JOIN appointments a
    ON p.name = a.patient_name
    WHERE p.phone=%s
    ORDER BY a.id DESC
    LIMIT 1
    """, (phone,))

    patient = cursor.fetchone()

    if patient:

        return {
            "name": patient[0],
            "age": patient[1],
            "gender": patient[2],
            "doctor": patient[3],
            "problem": patient[4]
        }

    return {}

@app.route('/reports')
def reports():

    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]

    cursor.execute("""
    SELECT *
    FROM appointments
    ORDER BY appointment_date DESC
    """)
    appointments = cursor.fetchall()

    return render_template(
        'reports.html',
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        appointments=appointments
    )

@app.route('/billing', methods=['GET', 'POST'])
def billing():

    # Generate Bill

    if request.method == 'POST':

        patient_name = request.form['patient_name']
        phone_number = request.form['phone_number']
        doctor_name = request.form['doctor_name']

        consultation_fee = int(request.form['consultation_fee'])
        medicine_fee = int(request.form['medicine_fee'])
        test_fee = int(request.form['test_fee'])

        total_amount = (
            consultation_fee +
            medicine_fee +
            test_fee
        )

        bill_date = datetime.now()

        cursor.execute("""
        INSERT INTO bills
        (
        patient_name,
        phone_number,
        doctor_name,
        consultation_fee,
        medicine_fee,
        test_fee,
        total_amount,
        bill_date
        )
                       
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
        patient_name,
        phone_number,
        doctor_name,
        consultation_fee,
        medicine_fee,
        test_fee,
        total_amount,
        bill_date
        ))

        conn.commit()

        flash("Bill Generated Successfully ✅")

    # Search Bills

    search = request.args.get('search', '')

    cursor.execute("""
    SELECT *
    FROM bills
    WHERE patient_name LIKE %s
       OR doctor_name LIKE %s
    ORDER BY id DESC
    """,
    (
        f"%{search}%",
        f"%{search}%"
    ))

    bills = cursor.fetchall()

    return render_template(
        'billing.html',
        bills=bills,
        search=search
    )

@app.route('/print_bill/<int:id>')
def print_bill(id):

    cursor.execute(
        "SELECT * FROM bills WHERE id=%s",
        (id,)
    )

    bill = cursor.fetchone()

    if 'admin' in session:
        user_type = "admin"

    elif 'patient_phone' in session:
        user_type = "patient"

    else:
        user_type = "guest"

    return render_template(
        'print_bill.html',
        bill=bill,
        user_type=user_type
    )

@app.route('/export_pdf')
def export_pdf():

    pdf_file = "appointments_report.pdf"

    p = canvas.Canvas(pdf_file)

    p.drawString(
        100,
        800,
        "Hospital Appointment Report"
    )

    p.save()

    return send_file(
        pdf_file,
        as_attachment=True
    )

@app.route('/export_excel')
def export_excel():

    cursor.execute("SELECT * FROM appointments")
    data = cursor.fetchall()

    df = pd.DataFrame(
        data,
        columns=[
            'ID',
            'Patient',
            'Doctor',
            'Problem',
            'Date',
            'Token',
            'Status',
            'Phone',
            'Patient_Phone'
        ]
    )

    file_name = "appointments_report.xlsx"

    df.to_excel(file_name, index=False)

    return send_file(
        file_name,
        as_attachment=True
    )



if __name__ == '__main__':
    app.run(debug=True)