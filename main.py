# REQUIREMENTS 
from flask import Flask, render_template, request , session , redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import datetime
import json
from flask_mail import Mail


#REGARDING BILL 
from io import BytesIO
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas




with open('config.json','r')as c:
    params=json.load(c)["params"]


local_server=True


app = Flask(__name__)

app.secret_key = 'super-secret-key'


app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USE_TLS = False,
    MAIL_USERNAME = 'developernachiket@gmail.com',
    MAIL_PASSWORD=  'rssqpznwvusseaxr'
)

mail=Mail(app)


# configure the MySQL database
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']


db = SQLAlchemy(app) 





# CLASSES 
class Contacts(db.Model):
    __tablename__ = 'Contacts' # set the table name
    Serial_num = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), unique=False, nullable=False)
    Phone_no = db.Column(db.String(45), nullable=False)
    Message = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(30), nullable=True)
    Email = db.Column(db.String(35), nullable=False)
    Rating=db.Column(db.Integer)



class AddVehicle(db.Model):
    __tablename__='AddVehicle' 
    Serial_num = db.Column(db.Integer, primary_key=True)
    Vehicle_name = db.Column(db.String(80), unique=False, nullable=False)
    Vehicle_num = db.Column(db.String(80), unique=False, nullable=False)
    Owner_name = db.Column(db.String(80), unique=False, nullable=False)
    Phone_no = db.Column(db.String(45), nullable=False)
    Entry_time = db.Column(db.Integer, nullable=True)
    Vehicle_type=db.Column(db.String(80), unique=False, nullable=False)
    Date = db.Column(db.String(30), nullable=True)




# class Vehicles_Track(db.Model):
#     __tablename__='Vehicles_Track'
    





@app.route("/")
def home():
    return render_template("index.html")





no_of_slots=15




@app.route("/pricing")
def pricing():
    return render_template("details.html")







# LOGIN SECTION 
@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    
    if ('user' in session and session['user']==params['admin_user']):
        return render_template("dashboard.html")
    
    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')

        if(username==params['admin_user'] and userpass==params['admin_pass']):
            session['user']=username
            return render_template("dashboard.html")

    return render_template("login.html")







now = datetime.datetime.now()



# Add a vehicle
@app.route("/addvehicle", methods=['GET','POST'])
def add_vehicle():
    vehiclename = ''

    if AddVehicle.query.count() == 0:
        # Add the first vehicle
        vehiclenum = request.form.get('vehiclenum')
        vehiclename = request.form.get('vehiclename')
        phone = request.form.get('phone')
        ownername = request.form.get('ownername')
        vehicle_type = request.form.get('vtype')
        entry_time = request.form.get('entrytime')
        timetype = request.form.get('timetype')

        entry_time = int(entry_time)
        if timetype == "PM":
            entry_time += 12
        

        entry = AddVehicle(Vehicle_name=vehiclename, Vehicle_num=vehiclenum, Phone_no=phone, Owner_name=ownername, Entry_time=entry_time, Vehicle_type=vehicle_type, Date=datetime.datetime.now())

        db.session.add(entry)
        db.session.commit()




    if request.method == 'POST':
        vehiclenum = request.form.get('vehiclenum')
        vehiclename = request.form.get('vehiclename')        
        phone = request.form.get('phone')        
        ownername = request.form.get('ownername') 
        vehicle_type=request.form.get('vtype')
        entry_time = request.form.get('entrytime')
        timetype = request.form.get('timetype')

        entry_time=int(entry_time)
        if timetype == "PM":
            entry_time += 12

        if no_of_slots == AddVehicle.query.count():
            message = "Sorry! All slots are filled. No more slots available for parking."
            return render_template("addvehicle.html", message=message)
        
    
        

        
        db.session.commit() 


        entry = AddVehicle(Vehicle_name=vehiclename,Vehicle_num=vehiclenum, Phone_no=phone,Owner_name=ownername , Entry_time=entry_time,Vehicle_type=vehicle_type,Date=datetime.datetime.now()) 

        db.session.add(entry)
        db.session.commit() 

    

    message=f"\t\tVehicle added successfully"
    return render_template("addvehicle.html",message=message)







@app.route("/slotstatus")
def about():
    slots_1 = db.session.query(AddVehicle).count()
    slots=(no_of_slots-slots_1)+1

    if(slots<=0):
        slots=0

    return render_template("slotstatus.html",slots=slots)








@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        vehiclenum = request.form.get('vehiclenum')
        entry = AddVehicle.query.filter_by(Vehicle_num=vehiclenum).first()

        if entry is None:
            decider=0
            message = f"Vehicle {vehiclenum} not found in the parking lot"
            return render_template("search.html", message=message,decider=decider)

        message = f"Vehicle found"
        decider=1
        return render_template('search.html', message=message, entry=entry,decider=decider)
    
    return render_template('search.html')



@app.route("/removevehicle", methods=['GET','POST'])
def remove_vehicle():


    if request.method == 'POST':
        vehiclenum = request.form.get('vehiclenum')

        
        entry = AddVehicle.query.filter_by(Vehicle_num=vehiclenum).first()

        if entry is None:
            message = f"Vehicle {vehiclenum} not found in the parking lot"
            return render_template("removevehicle.html", message=message)

        timetype = request.form.get('timetype')
        
        exit_time = int(request.form.get('exittime'))
        if(timetype=="PM"):
            exit_time+=12
       
        entry_time =entry.Entry_time
        duration=(exit_time-entry_time)
        vtype=request.form.get('vtype')
        no_of_day=int(request.form.get('days'))


        
        #Bill amount calculation
        if(vtype=="car"):
            rate_per_hour = 10
            day_charge=240

        elif(vtype=="bike"):
            rate_per_hour=5
            day_charge=120
        
        bill_amount =(duration * rate_per_hour) + (day_charge * no_of_day)

        
        db.session.commit()

        db.session.delete(entry)
        db.session.commit()




        #PDF Bill generation
        buffer = BytesIO()

        p = canvas.Canvas(buffer, pagesize=letter)

        p.drawString(250, 720, "PARKING RECEIPT")
        p.drawString(100, 670, f"Vehicle Number: {vehiclenum}")
        p.drawString(100, 640, f"Entry Time: {entry_time}:00 HRS")
        p.drawString(100, 610, f"Exit Time: {exit_time}:00 HRS")
        p.drawString(100, 580, f"Duration of Stay:{no_of_day} days {duration} hours")
        p.drawString(100, 550, f"Rate per hour: {rate_per_hour}")
        p.drawString(100, 520, f"Bill Amount: {bill_amount} INR")
        p.drawString(210, 490, f"Scan the QR code to pay bill online")

        img_file="/home/nachiket/Rppoop Project - Parking management system/static/assets/img/qr.jpeg"
        p.drawImage(img_file,x=200,y=250,height=200,width=200)


        p.showPage()
        p.save()


        buffer.seek(0)

        response = make_response(buffer.getvalue())

        #Responce objects headers are set to indicate that it contains a pdf file
        response.headers["Content-Disposition"] = "attachment; filename=parking_bill.pdf"
        response.headers["Content-Type"] = "application/pdf"

        
        return response

    return render_template("removevehicle.html")







@app.route("/contact", methods=['GET','POST'])
def contact():

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')        
        rating=request.form.get('rating')
        phone = request.form.get('phone')        
        message = request.form.get('message')  

        entry = Contacts(Name=name, Email=email, Phone_no=phone,Rating=rating ,Message=message, Date=datetime.datetime.now()) 

        db.session.add(entry)
        db.session.commit()  

        mail.send_message('New message from '+ name+' - Parking Management System',sender=email,recipients=[params['gmail-user']],body=message+"\n\nContact Number: "+phone)   


    return render_template("contact.html")







@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')






@app.route("/index")
def homee():
    return render_template("index.html")







@app.route("/details")
def details():
    return render_template("details.html")








@app.route("/parkedvehicles", methods=['GET','POST'])
def parkedvehicles():
    if ('user' in session and session['user']==params['admin_user']):
        posts=AddVehicle.query.all();
        return render_template("parkedvehicles.html",posts=posts,params=params)
    
    if request.method=='POST':
        
        username = request.form.get('uname')
        userpass = request.form.get('pass')

        if(username==params['admin_user'] and userpass==params['admin_pass']):
            session['user']=username
            posts=AddVehicle.query.all();
            return render_template("parkedvehicles.html",posts=posts,params=params)

        


if __name__ == '__main__':
    app.run(debug=True)

    
