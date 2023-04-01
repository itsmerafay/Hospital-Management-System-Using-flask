from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,logout_user,login_manager,LoginManager
from flask_login import login_required,current_user
from flask_mail import Mail
from sqlalchemy.sql import text
import json
import pdfkit
from flask import make_response
from flask_mail import Message


# MY db connection
local_server= True
app = Flask(__name__)
app.secret_key='abdulrafayatiq'

with open('config.json','r') as c:
    params = json.load(c)["params"]


#SMTP is Send Mail Transfer Protocol
# app.config.update(
    # MAIL_SERVER = 'smtp.gmail.com',
    # MAIL_PORT = 465,
    # MAIL_USER_SSL = True,
    # MAIL_USERNAME = params['gmail-user'],
    # MAIL_PASSWORD = params['gmail-password']
    
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'abdulrafayatiq.03@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ditggsgstbkhhccm'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['WKHTMLTOPDF_PATH'] = 'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe' # specify the path to wkhtmltopdf here
# )

mail = Mail(app)



# this is for getting unique user access # 
login_manager = LoginManager(app)          # initialize LOGIN MANAGER #
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/databas_table_name'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/hms'           ##we have initialize sqlalchemy database
db=SQLAlchemy(app)

## we willl create db models that is table
class Test(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
 
class User(UserMixin,db.Model):  # We use Usermixin to check if login credentials provide is correct or not #
     id = db.Column(db.Integer,primary_key=True)
     username = db.Column(db.String(50))
     email =  db.Column(db.String(50),unique=True)
     password = db.Column(db.String(1000))

class Patients(db.Model):         #making model for the tables of patient
     pid = db.Column(db.Integer,primary_key=True)
     email =  db.Column(db.String(50))
     name =  db.Column(db.String(50))
     gender =  db.Column(db.String(50))
     slot =  db.Column(db.String(50))
     disease =  db.Column(db.String(50))
     time=  db.Column(db.String(50), nullable=False)
     date =  db.Column(db.String(50),nullable=False)
     dept =  db.Column(db.String(50))
     doctor_name =  db.Column(db.String(50))
     number =  db.Column(db.String(50))

class Doctors(db.Model):         #making model for the tables of patient
     did = db.Column(db.Integer,primary_key=True)
     email =  db.Column(db.String(50))
     dept = db.Column(db.String(50))
     doctor_name =  db.Column(db.String(50))
    
    

# here we will pas end points and run the funtions
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/doctors',methods=['POST','GET'])
def doctors():
    global dept, doctor_name
    if request.method=="POST":

        email=request.form.get('email')
        dept=request.form.get('dept')
        doctor_name=request.form.get('doctor_name')

        query=db.engine.execute(f"INSERT INTO `doctors` (`email`,`dept`,`doctor_name`) VALUES ('{email}','{dept}','{doctor_name}')")
        flash("Information is Stored","primary")

    return render_template('doctors.html')

###################################################################

#####################################################################

# Function to generate PDF from appointment details
def generate_pdf(appointment_details):
    html = render_template('pdf_template.html', appointment=appointment_details)
    options = {'page-size': 'Letter', 'encoding': 'UTF-8'}
    pdf = pdfkit.from_string(html, False, options=options, configuration=pdfkit.configuration(wkhtmltopdf=app.config['WKHTMLTOPDF_PATH'])) # specify the path to wkhtmltopdf in the options parameter
    return pdf

# Function to send email with PDF attachment
def send_appointment_email(appointment_details, recipient):
    pdf_file = generate_pdf(appointment_details)
    with app.app_context():
        msg = Message('Appointment Details', sender='noreply@example.com', recipients=[recipient])
        msg.html = render_template('pdf_template.html', appointment=appointment_details)
        msg.attach(filename='pdf_template.html.pdf', data=pdf_file, content_type='application/pdf')
        mail.send(msg)

@app.route('/patients',methods=['POST','GET'])
@login_required
def patient():
    doct=db.engine.execute("SELECT * FROM `doctors`")

    if request.method=="POST":
        email=request.form.get('email')
        name=request.form.get('name')
        gender=request.form.get('gender')
        slot=request.form.get('slot')
        disease=request.form.get('disease')
        time=request.form.get('time')
        date=request.form.get('date')
        dept=request.form.get('dept')
        doctor_name = request.form.get('doctor_name')
        number=request.form.get('number')
        subject="Medicare Hospital"
        query=db.engine.execute(f"INSERT INTO `patients` (`email`,`name`,`gender`,`slot`,`disease`,`time`,`date`,`dept`,`doctor_name`,`number`) VALUES ('{email}','{name}','{gender}','{slot}','{disease}','{time}','{date}','{dept}','{doctor_name}','{number}')")

        # Send appointment details as PDF attachment via email
        appointment_details = {'name': name, 'gender': gender, 'slot': slot, 'disease': disease, 'time': time, 'date': date, 'dept': dept, 'number': number}
        send_appointment_email(appointment_details, email)

        # Flash message for booking confirmation
        flash("Booking Confirmed","info")

        # Render PDF for download
        pdf = generate_pdf(appointment_details)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=pdf_template.pdf'
        return response

    return render_template('patients.html',doct=doct)


@app.route('/booking')
@login_required
def bookings():
        if not User.is_authenticated:
            return render_template('login.html')
            
        if User.is_authenticated:
            em = current_user.email    
            if em=="admin@gmail.com":
                query=db.engine.execute(f"SELECT * FROM `patients`")
                return render_template('booking.html',query=query)
            
            else:
                em = current_user.email                                            
                query=db.engine.execute(f"SELECT * FROM `patients` WHERE email='{em}' ")
                return render_template('booking.html',query=query)
            
        return render_template('booking.html')



with open('config.json','r') as c:
    params = json.load(c)["params"]


#SMTP is Send Mail Transfer Protocol
# app.config.update(
    # MAIL_SERVER = 'smtp.gmail.com',
    # MAIL_PORT = 465,
    # MAIL_USER_SSL = True,
    # MAIL_USERNAME = params['gmail-user'],
    # MAIL_PASSWORD = params['gmail-password']
    

# @app.route('/contact')
# @login_required
# def contact(recipient):
#         email = request.form['email']
#         name = request.form['name']
#         subject = request.form['subject']
#         phone_number = request.form['phone_number']
#         message = request.form['message']

#         msg = Message(subject, sender='noreply@example.com', recipients=[recipient])

#         msg.body = f"Email: {email}\nPhone number: {phone_number}\nMessage: {message}"
#         mail.send(msg)

#         return 'Message sent successfully!'

    

#         return render_template('contact.html')


@app.route('/contact', methods=['POST', 'GET'])
@login_required
def contact():
    if request.method == 'POST':
        user_email = request.form['user_email']
        user_name = request.form['user_name']
        user_subject = request.form['user_subject']
        user_phone_number = request.form['user_phone_number']
        user_message = request.form['user_message']
        recipient = 'abdulrafayatiq.03@gmail.com'  # replace with your email address

        msg = Message(user_subject, sender='abdulrafayatiq.03@gmail.com', recipients=[recipient])
        msg.body = f"Name: {user_name}\nEmail: {user_email}\nPhone number: {user_phone_number}\nMessage: {user_message}"
        mail.send(msg)

        flash("Message Conved To Us Successfully","primary")

    return render_template('contact.html')

    # em = current_user.email                                            
    # query=db.engine.execute(f"SELECT * FROM `patients` WHERE email='{em}' ")
    # return render_template('booking.html',query=query)
    # if not User.is_authenticated:
        
    #     return render_template('login.html')
    # else:
    #     return render_template('booking.html',username=current_user.username)
    # return render_template('booking.html')


# @app.route('/edit/<string:pid>',methods=['POST','GET'])
# @login_required
# def edit(pid):
#     posts = Patients.query.filter_by(pid=pid).first() ## we re doing this to get the specific id # first = all data will be here now wrt id
#     if request.method=="POST":
#         email = request.form.get('email')
#         name = request.form.get('name')
#         gender = request.form.get('gender')
#         slot = request.form.get('slot')
#         disease = request.form.get('disease')
#         time = request.form.get('time')
#         date = request.form.get('date')
#         dept = request.form.get('dept')
#         number = request.form.get('number')
#         db.engine.execute(f"UPDATE `patients` SET `email` = '{email}', `name` = '{name}', `gender` = '{gender}', `slot` = '{slot}', `disease` = '{disease}', `time` = '{time}', `date` = '{date}', `dept` = '{dept}', `number` = '{number}' WHERE `patients`.`pid` = {pid}")
#         flash("Slot is Updates","success")
#         return redirect('/bookings')
    
# #     return render_template('edit.html',posts=posts)


@app.route("/edit/<string:pid>",methods=['POST','GET'])
@login_required
def edit(pid):
    posts=Patients.query.filter_by(pid=pid).first()
    if request.method=="POST":             
        if User.is_authenticated:
            em = current_user.email    
            if em=="admin@gmail.com":
                query=db.engine.execute(f"SELECT * FROM `patients`")
                return render_template('booking.html',query=query)
            
                email=request.form.get('email')
                name=request.form.get('name')
                gender=request.form.get('gender')
                slot=request.form.get('slot')
                disease=request.form.get('disease')
                time=request.form.get('time')
                date=request.form.get('date')
                dept=request.form.get('dept')
                number=request.form.get('number')
                db.engine.execute(f"UPDATE `patients` SET `email` = '{email}', `name` = '{name}', `gender` = '{gender}', `slot` = '{slot}', `disease` = '{disease}', `time` = '{time}', `date` = '{date}', `dept` = '{dept}', `number` = '{number}' WHERE `patients`.`pid` = {pid}")
                flash("Slot is Updates","success")
                return redirect('/patients')
            
                return render_template('edit.html',posts=posts)



@app.route("/delete/<string:pid>",methods=['POST','GET'])
@login_required
def delete(pid):
    db.engine.execute(f"DELETE FROM `patients`  WHERE `patients`.`pid`={pid}")
    flash('Slot Deleted Successfully','danger')
    return redirect('/booking')



@app.route('/signup',methods=['POST','GET'])
def signup():  
    if request.method=="POST":
        username=request.form.get('username')
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exists","warning")
            return render_template("/signup.html")
        encpassword = generate_password_hash(password)
        new_user=db.engine.execute(f"INSERT INTO `user` (`username`,`email`,`password`) VALUES ('{username}','{email}','{encpassword}')")        

        #another method for database connection for username email and password        
        # newuser = User(username=username,email=email,password = encpassword)
        # db.session.add(newuser)
        # db.session.commit()
        
        flash("Signup Successfully ")
        
        return render_template('login.html') 
    
    return render_template('signup.html')

@app.route('/login',methods = ['POST','GET'])
def login():
    if request.method=="POST":
        
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Logged In Successfully","primary")
            return redirect(url_for('index'))
        
        else:
            flash("Invalid Credentials","danger")
            return render_template('login.html')    
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successfully","warning")
    return redirect(url_for('login'))



 

@app.route('/test')
def test():
    try:
        Test.query.all()                ## whatever the data is just get them all
        return 'My database is connected'
    except:
        return 'My db is not connected'




app.run(debug=True)    






















    #     if email=="admin@gmail.com":
    #         db.engine.execute(f"UPDATE `patients` SET `email` = '{email}', `name` = '{name}', `gender` = '{gender}', `slot` = '{slot}', `disease` = '{disease}', `time` = '{time}', `date` = '{date}', `dept` = '{dept}', `number` = '{number}' WHERE `patients`.`pid` = {pid}")
    #         flash("Slot is Updated","success")
    #         return redirect('/booking')        
    #     else:
    #         db.engine.execute(f"SELECT * FROM `patients` WHERE `email` = '{email}', `name` = '{name}', `gender` = '{gender}', `slot` = '{slot}', `disease` = '{disease}', `time` = '{time}', `date` = '{date}', `dept` = '{dept}', `number` = '{number}' WHERE `patients`.`pid` = {pid} ")
    #         return redirect('/booking')
        
    # return render_template("edit.html",posts=posts)