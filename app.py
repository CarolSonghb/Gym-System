from flask import Flask, render_template, redirect, url_for, flash, request, session, abort
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask_login import  login_required
from functools import wraps
from webforms import LoginForm, RegisterForm, SearchForm, NewsForm, AttendanceForm,  DateSelectForm, DatePickerForm, TrainerScheduleForm
from models import User, AddMember, Admin, Trainer, Member, GroupClass, Report, News, Attendance
import mysql.connector
import connect
import json
import plotly
import plotly.express as px
import pandas as pd
import math

User = User()
AddMember = AddMember()
Admin = Admin()
Member = Member()
Trainer = Trainer()
GroupClass = GroupClass()
Report = Report()
News = News()   
Attendance = Attendance()

# Create A Flask Instance
app = Flask(__name__)
# secret key for the session
app.secret_key = "secret"
# secret key for the wtform
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'



time_now= datetime.strptime('2023-03-31 12:05:00', '%Y-%m-%d %H:%M:%S')
time_out = datetime.strptime('2023-03-31 13:05:00', '%Y-%m-%d %H:%M:%S')
current_date = time_now.date()
current_time = time_now.time()
# function for sql connection
db = mysql.connector.connect(
    host=connect.dbhost, user=connect.dbuser, password=connect.dbpass, database=connect.dbname)
cursor = db.cursor(buffered=True)


def catch_exception(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return render_template('500.html', error=e), 500
    return decorated_function


def login_required(f):
    @wraps(f)
    def innerfunc(*args, **kwargs):
        if session.get('logged_in'):
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return innerfunc

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error=e), 404

# Route for home page
@app.route('/')
@catch_exception
def home():
    try:
        return render_template('home.html')
    except IndexError:
        abort(404)
    


# Route for login page
@app.route('/login', methods=['POST', 'GET'])
@catch_exception
def login():
    form = LoginForm()
    # validate the form
    if form.validate_on_submit():
        # First check if it's an existing member.
        member = User.get_member(form.email.data)
        if member:
       
            session['user'] = member
            session['logged_in'] = True
            session['userid'] = member[0]
            session['user_type'] = 'Member'
            if User.validate_membership(member[0]) == False:
                # If the membership has expired or is inactive.
                flash('Your membership has expired or is inactive. Please contact the admin.')
                return redirect(url_for('login'))
            else:
                # redirect to member page once logged in
                return redirect(url_for('member'))
        # If not a member, check if it's a staff.
        else:
            staff = User.get_staff(form.email.data)
           
            if staff:
                session['user'] = staff
                session['logged_in'] = True
                session['userid'] = staff[0]
                session['user_type'] = staff[-3]
                if session['user_type'] == 'Trainer':
                    return redirect(url_for('trainer'))
                elif session['user_type'] == 'Admin' or session['user_type'] == 'Manager':
                    return redirect(url_for('admin'))
            # If neither a staff nor a member.
            else:
                flash("Invalid Email Address, please try again or register.")
                return redirect(url_for('login'))           
    # Visit by "GET" method.
    else:
        # redirect to member page once logged in
        return render_template('login.html', form=form)
# Route for register page


@app.route('/register', methods=['POST', 'GET'])
@catch_exception
def register():
    
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        dob = form.dob.data
        phone = form.phone.data
        address = form.address.data
        payment_frequency = form.payment_frequency.data
        medical_conditions = form.health_condition.data
        

        # Check to see if the email is already taken.
        if AddMember.validate_email(email) == False:
            flash('The email address is already taken. Please choose a different one.')
            return redirect(url_for('register', form=form))
        
        elif AddMember.validate_date(dob) == False:
            # Check to see if the user is 16 years old or above.
            flash('You must be 16 years old or above to register.')
            return redirect(url_for('register', form=form))
        
        elif AddMember.vallidate_phone(phone) == False:
            flash('Please enter a valid phone number.')
            return redirect(url_for('register', form=form))

        else:  
            # Insert the new user into the database
            # Get the new user's id.
            new_id = AddMember.add_member(email, first_name, last_name, dob, phone, address, payment_frequency, medical_conditions)

            # Add the new user's subscription into the database.
            AddMember.add_subscription(new_id, payment_frequency)

            if session.get('logged_in'): 
                flash('New member added successfully.')
                return redirect(url_for('admin'))
            else:                                                                    
                flash('Registration Successful. Please login to continue.')
                return redirect(url_for('login'))
       
    else:
        return render_template('register.html', form=form)


# route for admin to add new member
@app.route('/admin/add_member', methods=['POST', 'GET'])
@catch_exception
@login_required
def add_member():
    return redirect(url_for('register'))




# route for admin portal
@app.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():
    if session['logged_in'] == True:
        staff_id = session['userid']
        form = SearchForm()
        staff_info = Admin.get_staff_info(staff_id)
        return render_template('admin.html', staff_id=staff_id, staff_info=staff_info, form=form)
    else:
        return redirect(url_for('login'))
   

@app.route('/admin/search', methods=['POST', 'GET'])
@catch_exception
@login_required
def search():
    staff_id = session['userid']
    is_admin = True
    form = SearchForm()
    if form.validate_on_submit():
        search = form.search.data

        # query the database to get payment frequency options
        payment_frenquecy = Member.get_payment_frequency()
        
        # check search input against member table
        results = Admin.search_member(search)

        return render_template('member_details.html', staff_id=staff_id, results=results, form=form, is_admin=is_admin, pmf= payment_frenquecy)


# route for admin to track attendance
@app.route('/admin/attendace', methods=['POST', 'GET'])
@catch_exception
def check_attendance():
    if 'staff' in session:
        staff_id = session['user'][0]
        return render_template('attendance.html', staff_id=staff_id)
    else:
        return redirect(url_for('login'))


# route for admin to edit profile


@app.route('/admin/<member_id>/edit', methods=['POST', 'GET'])
@catch_exception
@login_required
def admin_edit(member_id):
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        dob = request.form.get('dob')
        payment_frequecy = request.form.get('payment_frequency')
        phone = request.form.get('phone')
        address = request.form.get('address')
        health_condition = request.form.get('health_condition')
        email = request.form.get('email')
        # if AddMember.vallidate_phone(phone) == False:
        #     flash('Please enter a valid phone number.')
        #     return redirect(url_for('admin_edit', member_id=member_id))
        
        Member.admin_edit_member(firstname, lastname, dob, payment_frequecy, phone, address, health_condition,email, member_id )
        flash("Member information has been updated successfully.")  
        return redirect(url_for('admin'))


# Trainer Schedule check for Admins/Manager.

@ app.route('/admin/trainer_schedule', methods=['GET','POST'])
@catch_exception
@login_required
def admin_trainer_schedule():
    form = TrainerScheduleForm()   
    if form.validate_on_submit():
        start_date = form.start_date.data
        ending_date=form.ending_date.data
        trainer = form.select_trainer.data
        if trainer == 'All':
            results, column_names = Trainer.get_all_trainers_schedule(start_date,ending_date)
            
        else:
            results, column_names = Trainer.get_trainer_schedule(trainer, start_date,ending_date)
        return render_template('admin_trainer_schedule.html',form=form, results=results, column_names=column_names)
    else:
        return render_template('admin_trainer_schedule.html', form=form)

# Admin to check expiring membership
@ app.route('/admin/expiring_membership', methods=['GET','POST'])
@catch_exception
@login_required
def expiring_membership():
    results, column_names = Admin.check_expiring_members(current_date)
    if not results:
        flash('No expiring membership found.')
        return redirect(url_for('admin_expiring_membership'))
    else:
        return render_template('membership_expiring.html',results=results, column_names=column_names, number=len(results))



# route for admin to delete profile

@app.route('/admin/deactive/<member_id>', methods=['POST', 'GET'])
@catch_exception
@login_required
def member_deactive(member_id):
    Admin.deactivate_member(member_id)
    flash('Member has been deactivated successfully.')
    return redirect(url_for('admin'))


# Generate attendance report for both Admins and Manager.
@ app.route('/admin/attendance_report', methods=['GET','POST'])
@catch_exception
@login_required
def attendance_report():
    form = DateSelectForm()
    if form.validate_on_submit():
        starting_date=form.start_date.data
        ending_date=form.ending_date.data
        attendance_records,column_names = Report.attendance_report(starting_date,ending_date)
        total_visits = Report.total_visits(starting_date,ending_date)
        attendance_number = Report.attendance_number(starting_date,ending_date)
     
        df = pd.DataFrame(attendance_number, columns=['Type of Visit', 'Date', 'Number'])

        # create the plot
        fig = px.line(df, x='Date', y='Number', color='Type of Visit', title='Attendance Report')
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
  
        return render_template('attendance_report.html',form=form, column_names=column_names,records=attendance_records,total_visits = total_visits, graphJSON=graphJSON)
    else:
        return render_template('attendance_report.html',form=form)
    



# Generate revenue report for both Admins and Manager.
@ app.route('/admin/revenue_report', methods=['GET','POST'])
@catch_exception
@login_required
def revenue_report():
    form = DateSelectForm()
    if form.validate_on_submit():
        start_date=form.start_date.data
        ending_date=form.ending_date.data
        try:
            revenue, total_revenue = Report.total_revenue_report(start_date,ending_date)
            df = pd.DataFrame(revenue, columns=["Type of Income", "Number of Attendances", "Income"])
            fig = px.pie(df, values='Income', names='Type of Income', color='Type of Income',title="Revenue Report")
            graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        except Exception:
            flash('No revenue found.')
            return redirect(url_for('revenue_report'))
        
        return render_template('revenue_report.html', form=form, revenue=revenue,  total_revenue=total_revenue, graphJSON = graphJSON )
    else:
        return render_template('revenue_report.html',form=form)


# Manager-only function, rank all classes by total attendance.
@ app.route('/manager/class_ranking', methods=['GET','POST'])
@catch_exception
@login_required
def manager_class_ranking():
    form = DateSelectForm()

    if form.validate_on_submit():
        start_date=form.start_date.data
        ending_date=form.ending_date.data
        results, column_names = Report.class_ranking(start_date,ending_date)
        return render_template('manager_class_ranking.html',form=form, results=results, column_names=column_names)
    else:
        return render_template('manager_class_ranking.html',form=form)

# route for trainer portal
@app.route('/trainer', methods=['POST', 'GET'])
@catch_exception
@login_required
def trainer():
    if session['logged_in'] == True:
        trainer_id = session['user'][0]
        is_trainer = True
        form = SearchForm()
        trainer_info= Trainer.get_trainer_info(trainer_id)
        # query to get trainer's class schedule in the next 14 days
        class_schedule = Trainer.get_class_schedule(trainer_id, current_date)
     # query to get trainer's private training schedule in the next 14 days
        private_schedule = Trainer.get_private_schedule(trainer_id, current_date)
         
        return render_template('trainer.html', trainer_id=trainer_id, trainer_info=trainer_info, 
                               form=form, class_schedule=class_schedule, 
                               private_schedule=private_schedule, is_trainer=is_trainer)
    else:
        return redirect(url_for('login'))


# route for trainer to view trainer details
@app.route('/trainer_details/<trainer_id>', methods=['POST', 'GET'])
@catch_exception
@login_required
def trainer_details(trainer_id):
    trainer_info= Trainer.get_trainer_info(trainer_id)
    return render_template('trainer_details.html', trainer_id=trainer_id,
                            trainer_info=trainer_info)

# route for trainer to cancel booking

@ app.route('/trainer/<class_id>/<member_id>/cancel', methods=['POST', 'GET'])
@catch_exception
@login_required
def trainer_booking_delete(member_id, class_id):
    Member.cancel_booking(class_id, member_id)
    flash('Your booking has been successfully cancelled.')
    return redirect(url_for('trainer'))

# route for admin to edit profile
@app.route('/trainer/edit', methods=['POST', 'GET'])
@catch_exception
@login_required
def trainer_edit():
    trainer_id = session['user'][0]
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        phone = request.form.get('phone')
        dob = request.form.get('dob')
        about_me = request.form.get('about_me')
        photo_link = request.form.get('photo_link')
        if AddMember.vallidate_phone(phone) == False:
            flash('Please enter a valid phone number.')
            return redirect(url_for('trainer_edit'))
        Trainer.edit_trainer_info(firstname, lastname, phone, dob, about_me, photo_link, trainer_id)
        flash( 'Trainer ' + str(firstname) + ' '+ str(lastname) + ' information has been updated successfully.') 
        return redirect(url_for('trainer_details', trainer_id=trainer_id))
        
    else:
        return redirect(url_for('login'))
    

# check trainer's trainees name
@app.route('/trainer/trainees', methods=['POST', 'GET'])
@catch_exception
@login_required
def trainees():
        trainer_id = session['user'][0]
        
        #  qurery to get trainer's trainees
        trainees, column_names = Trainer.get_trainees(trainer_id, current_date)
      
        if trainees:
            return render_template('trainees.html', trainer_id=trainer_id, column_names=column_names, 
                                trainees=trainees)
        else:
            flash('You do not have any trainees booked for the upcoming sessions.')
            return redirect(url_for('trainer'))
        
        
# route for trainer to view member profile
@app.route('/trainer/profile/<member_id>', methods=['POST', 'GET'])
@catch_exception
@login_required
def member_profile(member_id):
    is_trainer = True
    # query the database by member id to get member's info
    results = Admin.search_member(member_id)
    
    return render_template('member_details.html', member_id=member_id, results=results, is_trainer=is_trainer)
   


# route to check all trainers
@app.route('/all_trainers/<member_id>', methods=['POST', 'GET'])
@catch_exception
@login_required
def all_trainers(member_id):
    # query the database to get all trainers
    trainers, column_names = Trainer.get_all_trainers()
    return render_template('all_trainers.html',column_names=column_names, trainers=trainers, member_id=member_id)


# route to view trainer's available sessions
@app.route('/trainer_sessions/<trainer_id>/<member_id>', methods=['POST', 'GET'])
@catch_exception
@login_required
def available_sessions(trainer_id, member_id):
    trainer_info= Trainer.get_trainer_info(trainer_id)
    form = DatePickerForm()
    if form.validate_on_submit():
        date = form.class_date.data
        if date < current_date:
            flash('Please choose a date from today onwards.')
            return redirect(url_for('available_sessions', trainer_id=trainer_id, member_id=member_id))
        else:
            available_slots = Trainer.get_available_slots(trainer_id, date)
            return render_template('trainer_session.html',  
                                trainer_detail=trainer_info, available_slots=available_slots, trainer_id=trainer_id, member_id=member_id, form=form, date=date)
    return render_template('trainer_session.html', trainer_detail=trainer_info, form=form, trainer_id=trainer_id, member_id=member_id)




# route to book a session
@app.route('/book_session/<trainer_id>/<member_id>/<date>', methods=['POST', 'GET'])
@catch_exception
@login_required
def book_session(trainer_id, member_id, date):
    if request.method == 'POST':
        time_slot = request.form.get('time_slot')
        
        slot_taken = GroupClass.check_slot(member_id, date, time_slot) 

        if slot_taken:
            flash('You have already made a booking at this time.')
            return redirect(url_for('available_sessions', trainer_id=trainer_id, member_id=member_id))
        else:
        # make new entry in timetable and booking table &  make payment for the session
            Member.book_session(trainer_id, date, time_slot, member_id, current_date)
            # get trainer's name
            trainer_name = Member.chosen_trainer(trainer_id)
            # get the booked time slot
            chosen_time = Member.chosen_time(time_slot)
            flash('You have successfully booked a private session with trainer ' + str(trainer_name) + ' on ' + str(date) + ' at timeslot ' + str(chosen_time))
            return redirect(url_for('member'))



# route for member profile  


@app.route('/member', methods=['POST', 'GET'])
@catch_exception
@login_required
def member():
    member_id = session['user'][0]
    is_member = True
    # query the database by member id to get member's info
    member_info = Member.get_member_info(member_id)

    # query the database by member id to check if membership will expired in next 15 days
    expiry_date = Member.check_membership_expiry(member_id)

    cursor.execute('''SELECT PaymentFrequency FROM paymentFrequency;''')
    payment_frenquecy = cursor.fetchall()

    # if membership has expired or will be expire in next 15 days, popup a message
    if expiry_date:
        # if alredy expired, popup a message
        if expiry_date[0] < current_date:
            flash('Your membership has expired on ' +
                  str(expiry_date[0]) + '. Please renew your membership through My Details.')
        # if not expired, remind the member to renew
        else:
            flash('Your membership will expire on ' +
                  str(expiry_date[0]) + '. Please renew your membership through My Details.')

    # query the database by member id to get member's booking
    member_booking = Member.get_member_booking(member_id, current_date)
    # # query the database to get payment frequency options
    # payment_frenquecy = Member.get_payment_frequency()

    return render_template('member_info.html', member_id=member_id, member_info=member_info, is_member=is_member, booking=member_booking, pmf=payment_frenquecy )

@app.route('/member/member_details')
@catch_exception
@login_required
def member_details():
    member_id = session['user'][0]
    is_member = True
    # query the database by member id to get member's info
    member_info = Member.get_member_info(member_id)
    # query the database to get payment frequency options
    cursor.execute('''SELECT PaymentFrequency FROM paymentFrequency;''')
    payment_frenquecy = cursor.fetchall()

    return render_template('member_details.html', member_id=member_id, results=member_info, is_member=is_member, pmf=payment_frenquecy )

# route for member to edit profile


@app.route('/member/<member_id>/edit', methods=['POST', 'GET'])
@catch_exception
@login_required
def member_edit(member_id):
    if request.method == 'POST':
        payment_frequency = request.form.get('payment_frequency')
        phone = request.form.get('phone')
        address = request.form.get('address')
        health_condition = request.form.get('health_condition')
        if AddMember.vallidate_phone(phone) == False:
            flash('Please enter a valid phone number.')
            return redirect(url_for('member_edit', member_id=member_id))
        Member.update_member_info(payment_frequency, phone, address, health_condition, member_id)
        
        flash( "Your personal details have been updated successfully." ) 
        return redirect(url_for('member'))

    else:
        return redirect(url_for('member'))


@app.route('/member/<member_id>/renew', methods=['POST', 'GET'])
@catch_exception
@login_required
def member_renew(member_id):
    payment_date = Member.get_payment_date(member_id)
    
    if request.method == 'POST':
        payment_frequecy = request.form['payment_frequecy']
        if payment_frequecy == 'Monthly':
            payment_amount = 30
            expiry_date = payment_date + relativedelta(months=+1)
        elif payment_frequecy == 'Half-Yearly':
            payment_amount = 150
            expiry_date = payment_date + relativedelta(months=+6)
        elif payment_frequecy == 'Yearly':
            payment_amount = 300
            expiry_date = payment_date + relativedelta(months=+12)
        Member.renew_subscription(expiry_date, payment_amount, member_id)
        flash("Your membership has been renewed successfully.")
        return redirect(url_for('member'))

    else:
        return redirect(url_for('member'))



# route for viewing group classes
@app.route('/group_classes', methods=['POST', 'GET'])
@catch_exception
@login_required
def group_classes():
    
    member_id = session['user'][0]
    # query to get all group classes in the next 14 days
    classes = GroupClass.get_group_classes(current_date)
    return render_template('group_class.html', classes=classes,  member_id = member_id)

# route for member to make booking with group classes
@app.route('/<member_id>/booking', methods=['POST', 'GET'])
@catch_exception
@login_required
def class_booking(member_id):

    if request.method == 'POST':
        class_id = request.form.get('class_id')
        slot_id = request.form.get('slot_id')
        class_date = request.form.get('class_date')
        slot_taken = GroupClass.check_slot(member_id, class_date , slot_id)
        # check if the member has already booked this class
        booked = GroupClass.check_booked_class(class_id, member_id)
        if booked:
            flash("You have already booked this class.")
            return redirect(url_for('group_classes'))
        elif slot_taken:
            flash("You have already made a booking at this time")
            return redirect(url_for('group_classes'))
        else:
            GroupClass.book_class(class_id, member_id, current_date)
            flash("You have successfully booked a class.")
            return redirect(url_for('member'))

    return render_template('group_class.html', member_id=member_id)


# route for member to view booked classes
@app.route('/member/attendance', methods=['POST', 'GET'])
@catch_exception
@login_required
def attendance():
    member_id = session['user'][0]
    booked_info = Member.check_attendance(current_date, member_id)
    return render_template('attendance.html', booked_info=booked_info)


# route for member to delete booking

@ app.route('/member/<class_id>/<member_id>/cancel', methods=['POST', 'GET'])
@catch_exception
@login_required
def booking_delete(member_id, class_id):
    Member.cancel_booking(class_id, member_id)
    flash('Your booking has been successfully cancelled.')
    return redirect(url_for('member'))




@ app.route('/attendance_tracker', methods=['POST', 'GET'])
@catch_exception
def attendance_tracker():
    form=AttendanceForm()
    if form.validate_on_submit():
        member_id = form.member_id.data
        # Check if member_id is valid, check upcoming class(starts within 1hour),flash prompt if invalid.
        member = User.check_member(member_id)
        
        if member:
            member_cheked_in = member[-1]
            member_name = member[1]
            if member_cheked_in == 1:
                checkout_time = time_out.strftime("%X")
                Attendance.member_checkout(current_date,checkout_time,member_id)
                flash("Thanks "+ member_name +", you have checked out. Have a great day!" ,"success" )
                return redirect(url_for('attendance_tracker'))
            elif member_cheked_in == 0:
                checkin_time = time_now
                # check if member has booked a class within 1 hour
                upcoming_booking = Attendance.get_upcoming_booking(time_now, member_id)
                if upcoming_booking:
                    class_id = upcoming_booking[0][0]
                    class_name = upcoming_booking[0][1]
                    class_time = upcoming_booking[0][2]
                    if class_name == 'Private Training': 
                        type_of_visit = 'Private Training'
                    else :
                        type_of_visit = 'Group Class'
                        # checkin the member and update the attendance table
                        Attendance.general_checkin(member_id,type_of_visit,current_date,checkin_time)  
                        Attendance.update_booking_attended(class_id, member_id)
                        flash("Hi, "+ member_name +". You have a " + class_name + " booking at " + str(class_time) +". You have checked in your booked class successfully!", "success")
                        return redirect(url_for('attendance_tracker'))
                else:
                    type_of_visit = 'General Visit'
                    # check in member as general visit
                    Attendance.general_checkin(member_id,type_of_visit,current_date,checkin_time)   
                    flash("Hi, "+ member_name +". You have checked in as general visit successfully!", "success")
                    return redirect(url_for('attendance_tracker'))

        else:
            flash("Invalid member ID. Please try again.", "error")
            return render_template('member_checkin.html',form=form)
    return render_template('member_checkin.html', form=form)
    



# news page


@ app.route('/news', methods=['POST', 'GET'])
@catch_exception
def news():
    # pagination for pages and limiting the number of news shown in one page
    current_page = request.args.get('page', 1, type=int)
    news_per_page = 3
    cursor.execute('''SELECT COUNT(NewsID) FROM news;''')
    total_news = cursor.fetchone()[0]
    pages = int(math.ceil(total_news / float(news_per_page))) #getting total pages
    start_index = (current_page - 1) * news_per_page #0
    end_index = start_index + news_per_page #3
    all_news = News.get_all_news()
    one_page = all_news[start_index:end_index]

    return render_template('news.html', one_page=one_page, pages=pages, current_page=current_page)

# create news page


@ app.route('/news_compose', methods=['POST', 'GET'])
@catch_exception
@login_required
def news_compose():
    if session['user_type'] == 'Admin' or session['user_type'] == 'Manager':
        staff_id = session['userid']
        form = NewsForm()
        title = form.title.data
        content = form.content.data
        date = form.date.data
        if form.validate_on_submit():
           
            News.add_news(staff_id, title, content, date)
            flash('Your news has been created!', 'success')
            return redirect(url_for('news'))
        return render_template('news_compose.html', form=form)


# single news page


@ app.route('/news/<news_id>', methods=['POST', 'GET'])
@catch_exception
def news_id(news_id):
    news = News.get_news(news_id)
    news=(news,)
    return render_template('news_readmore.html', news_id=news_id, news=news)


@ app.route('/news/edit/<news_id>', methods=['POST', 'GET'])
@catch_exception
@login_required
def news_edit(news_id):
    # get news content
    news = News.get_news(news_id)
    news_id = int(news[0])
    news_title = news[2]
    news_content = news[3]
    news_date = news[4]
    if session['user_type'] == 'Admin' or session['user_type'] == 'Manager':
        staff_id = session['userid']
        is_editing = True
        form = NewsForm(title=news_title, content=news_content, date=news_date)
        title = form.title.data
        content = form.content.data
        date = form.date.data
        if form.validate_on_submit():
            News.edit_news(staff_id, title, content, date, news_id)
            flash('Your news has been updated!')
            return redirect(url_for('news'))
        
        return render_template('news_compose.html', news_id=news_id, news_title =news_title, news_content=news_content, news_date=news_date, form=form, is_editing=is_editing  )
        
    return render_template('news_compose.html', news_id=news_id, news_title =news_title, news_content=news_content, news_date=news_date,  )



@ app.route('/news/delete/<news_id>', methods=['POST', 'GET'])
@catch_exception
@login_required
def news_delete(news_id):
    News.delete_news(news_id)
    flash('Your news has been deleted!')
    return redirect(url_for('news'))


# About page
@ app.route('/about', methods=['POST', 'GET'])
def about():
    return render_template('about.html')

# contact page


@ app.route('/contact', methods=['POST', 'GET'])
def contact():
    return render_template('contact.html')




@ app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    session.clear()
    flash('You have logged out')
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.secret_key = "secret"
    app.run(debug=True)
