from flask import Flask,render_template,redirect,request,session,redirect,url_for,g,flash,jsonify
import mysql.connector
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import random
import pyrebase
#firebase config
firebase_config = {"apiKey": "AIzaSyAxTQTF_Gfh30xKF337pzfChFRM2IrP-Fs",

  "authDomain": "pythonfacedetection-189b4.firebaseapp.com",

   "databaseURL":"https://pythonfacedetection-189b4-default-rtdb.firebaseio.com/",

  "projectId": "pythonfacedetection-189b4",

  "storageBucket": "pythonfacedetection-189b4.firebasestorage.app",

  "messagingSenderId": "459493321741",

  "appId": "1:459493321741:web:3b2ec7ea6a9ecbf952f944",

  "measurementId": "G-QDBB3PQMCP"
}
app = Flask(__name__)
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'cairocoders-ednalan'
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()
# MySQL connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'school'
}
conn=mysql.connector.connect(host='localhost',user='root',password='',database='school')
cur=conn.cursor()
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='school'
    )
def get_attendance_data(roll_number=None, date=None):
    if roll_number:
        # Fetch attendance for a specific student
        attendance_data = db.child("Attendance").order_by_child("Roll_No").equal_to(roll_number).get()
    elif date:
        # Fetch attendance for a specific date
        attendance_data = db.child("Attendance").order_by_child("Date").equal_to(date).get()
    else:
        # Fetch all attendance data
        attendance_data = db.child("Attendance").get()

    if attendance_data.each():
        response = ""
        for entry in attendance_data.each():
            attendance = entry.val()
            response += f"Roll No: {attendance['Roll_No']}, Name: {attendance['Name']}, Time: {attendance['Time']}<br>"
        return response
    else:
        return "No attendance data found."
def get_intents():
    with open('intents.json') as f:
        return json.load(f)
    
def match_intent(user_input):
    intents = get_intents()['intents']
    for intent in intents:
        for pattern in intent['patterns']:
            if pattern.lower() in user_input.lower():
                return intent  # Return the matched intent
    return None

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/register')
def register():
    return render_template('form.html')    
@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve form data
    user_type = request.form['user_type']
    roll_or_id = request.form['roll_or_id']
    name = request.form['name']
    age = request.form['age']
    department_or_class = request.form['department_or_class']
    email = request.form['email']
    password = request.form['password']

    hashed_password = generate_password_hash(password)

    # Map user type to the corresponding database table
    table_map = {
        "Student": "students",
        "Staff": "staff",
        "Faculty": "faculty"
    }

    target_table = table_map.get(user_type)  # Determine the target table based on user type
    if not target_table:
        flash("Invalid user type selected.", "error")
        return redirect(url_for('register'))

    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check if the user already exists in the respective table
        check_query = f"SELECT * FROM {target_table} WHERE roll_or_id = %s"
        cursor.execute(check_query, (roll_or_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash(f"Error: {user_type} with ID {roll_or_id} already exists!", "error")
            return redirect(url_for('register'))

        # Insert data into the respective table
        insert_query = f"""
        INSERT INTO {target_table} (roll_or_id, name, age, department_or_class, email, password, registration_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s ,  CURRENT_TIMESTAMP)
        """
        values = (roll_or_id, name, age, department_or_class, email , hashed_password)
        cursor.execute(insert_query, values)
        conn.commit()

        # Close connections
        cursor.close()
        conn.close()

        flash(f"Success: {user_type} registered successfully!", "success")
        return redirect(url_for('register'))

    except mysql.connector.Error as err:
        flash(f"Database Error: {err}", "error")
        return redirect(url_for('register'))

@app.route('/login_validation', methods=['POST'])
def login_validation():
    # Retrieve form data
    email = request.form.get('email')
    password = request.form.get('password')
    user_type = request.form.get('user_type')  # Add a dropdown in your login form for user type

    # Map user type to the corresponding table
    table_map = {
        "Student": "students",
        "Staff": "staff",
        "Faculty": "faculty"
    }

    target_table = table_map.get(user_type)
    if not target_table:
        flash("Invalid user type selected.", "error")
        return redirect('/')

    try:
        # Query the respective table for the email
        query = f"SELECT email, password FROM {target_table} WHERE email = %s"
        cur.execute(query, (email,))
        user = cur.fetchone()

        if user:
            # Validate the password
            stored_password_hash = user[1]  # Assuming password is the second column
            if check_password_hash(stored_password_hash, password):
                flash(f"You were successfully logged in as {user_type}!", "success")
                return redirect('/chat')
            else:
                flash("Invalid credentials! Incorrect password.", "error")
        else:
            flash("Invalid credentials! Email not found.", "error")

        return redirect('/')

    except mysql.connector.Error as err:
        flash(f"Database Error: {err}", "error")
        return redirect('/')

    except Exception as e:
        flash(f"Unexpected Error: {e}", "error")
        return redirect('/')
@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form.get('message')

    # Check if the input is requesting student details
    if user_input.lower().startswith('student'):
        try:
            # Extract roll number from the user input
            roll_number = int(user_input.split(' ')[1])
        except (IndexError, ValueError):
            return jsonify({'response': 'Please provide a valid roll number in the format: student <roll_or_id>'})
        
        try:
            # Connect to the database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            # Query to fetch full student details
            query = """
                SELECT 
                    roll_or_id, name, age,department_or_class, email 
                FROM students 
                WHERE roll_or_id = %s
            """
            cursor.execute(query, (roll_number,))
            result = cursor.fetchone()

            # Close database connections
            cursor.close()
            conn.close()

            # Format the chatbot response
            if result:
               response = (
                    f"<div style='font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;'>"
                    f"🆔 <strong>Roll Number:</strong> {result['roll_or_id']}<br>"
                    f"👤 <strong>Name:</strong> {result['name']}<br>"
                    f"🎂 <strong>Age:</strong> {result['age']} years<br>"
                    f"🏫 <strong>Class:</strong> {result['department_or_class']}<br>"
                    f"✉️ <strong>Email:</strong> {result['email']}<br>"
                    f"</div>"
                    )

            else:
                response = "⚠️ Student not found. Please check the roll number and try again."
        except mysql.connector.Error as err:
            response = f"🚨 Database Error: {err}"
    elif "attendance" in user_input.lower():
        if "for today" in user_input.lower():
            today_date = datetime.now().strftime("%Y-%m-%d")
            response = get_attendance_data(date=today_date)
        elif "student" in user_input.lower():
            try:
                roll_number = int(user_input.split(' ')[2])
                response = get_attendance_data(roll_number=roll_number)
            except (IndexError, ValueError):
                response = "Please provide a valid roll number for attendance."
    else:
        
        if match_intent(user_input):
            matched_intent = match_intent(user_input)
            response = random.choice(matched_intent['responses'])
        else:
            response = "i Did Not Understand..!"

    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
