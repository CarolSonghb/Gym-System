from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField,  TextAreaField, validators,IntegerField, ValidationError
import mysql.connector
import connect

# function for sql connection
db = mysql.connector.connect(
    host=connect.dbhost, user=connect.dbuser, password=connect.dbpass, database=connect.dbname)
cursor = db.cursor(buffered=True)

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[
        validators.input_required()])
    submit = SubmitField('Log In')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[
                        validators.input_required(), validators.Email()])
    first_name = StringField('First Name', validators=[
        validators.input_required()])
    last_name = StringField('Last Name', validators=[
                            validators.input_required()])
    dob = DateField('Date of Birth', validators=[
        validators.input_required()])
    
    phone = StringField('Phone', validators=[
                        validators.input_required()])
    address = StringField('Address', validators=[
                          validators.input_required()])
    payment_frequency = SelectField('Payment Frequency', choices=[('','Please select a preferred payment frequency'), ('Monthly', 'Monthly'), ('Half-Yearly', 'Half-Yearly'), ('Yearly', 'Yearly')], default='', validators=[
        validators.input_required()])  # monthly, half-yearly, yearly
    health_condition = StringField('Health Condition', validators=[
                                   validators.input_required()])
    submit = SubmitField('Register')

 

class SearchForm(FlaskForm):
    search = StringField('Search', validators=[
                         validators.input_required()])
    submit = SubmitField('Search')



class NewsForm(FlaskForm):
    title = StringField('Title', validators=[
                        validators.input_required()])
    content = TextAreaField('Content', validators=[
        validators.input_required()])
    date = DateField('Date', validators=[
        validators.input_required()])
    submit = SubmitField('Add')


class AttendanceForm(FlaskForm):
    member_id = IntegerField('Your Member ID',validators=[validators.input_required()])
    submit = SubmitField('Submit')


class DateSelectForm(FlaskForm):
    start_date = DateField('From', validators=[validators.input_required()])
    ending_date = DateField('To', validators=[validators.input_required()])
    submit = SubmitField('Submit')

class DatePickerForm(FlaskForm):
    class_date = DateField('Choose Date', validators=[validators.input_required()])
    submit = SubmitField('Submit')


class TrainerScheduleForm(FlaskForm):
    start_date = DateField('From', validators=[validators.input_required()])
    ending_date = DateField('To', validators=[validators.input_required()])
    # Get a list of all trainers
    cursor.execute('''SELECT CONCAT(FirstName,' ',LastName) FROM staff WHERE StaffType='Trainer' ORDER BY FirstName;''')
    db.commit()
    trainers=cursor.fetchall()
    trainers=[x[0] for x in trainers]
    trainers.insert(0,'All') 
    select_trainer = SelectField('Trainer',choices=trainers,validators=[validators.input_required()])
    submit = SubmitField('Submit')