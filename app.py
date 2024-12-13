from flask import Flask,render_template,redirect,request,session,redirect,url_for,g,flash,jsonify
import mysql.connector
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
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
conn=mysql.connector.connect(host='localhost',port='3306',user='root',password='',database='register')
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

@app.route('/login_validation',methods=['POST'])
def login_validation():
    email=request.form.get('email')
    password=request.form.get('password')
    hashed_password = generate_password_hash(password)
    cur.execute("SELECT * FROM `users` WHERE `email` = %s AND `password` = %s", (email, hashed_password))
    users = cur.fetchall()
    if len(users)>0:
        flash('You were successfully logged in')
        return redirect('chat')
    else:
        flash('Invalid credentials !!!')
        return redirect('/')

@app.route('/ask', methods=['POST'])
def ask():
    intents = get_intents()
    user_input = request.form.get('message')
    
    if user_input.lower().startswith('student'):
        try:
            roll_number = int(user_input.split(' ')[1])
        except (IndexError, ValueError):
            return jsonify({'response': 'Please provide a valid roll number.'})
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = "SELECT name, age, class FROM students WHERE roll_number = %s"
        cursor.execute(query, (roll_number,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            response = (
                f"Name: {result['name']}<br>"
                f"Age: {result['age']}<br>"
                f"Class: {result['class']}<br>"
            )
        else:
            response = "Student not found."
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
