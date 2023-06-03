from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import mysql.connector
import connect



timeNow = datetime.strptime('2023-03-31 12:05:00', '%Y-%m-%d %H:%M:%S')
current_date = timeNow.date()
current_time = timeNow.time()
# function for sql connection
db = mysql.connector.connect(
    host=connect.dbhost, user=connect.dbuser, password=connect.dbpass, database=connect.dbname)
cursor = db.cursor(buffered=True)




class User:
    def __init__(self, email=None, member_id=None):
        self.email = email
        self.member_id = member_id

    def get_member(self, email):
        cursor.execute('''SELECT * FROM member WHERE EmailAddress = %s''', (email,))
        return cursor.fetchone()

    def validate_membership(self, member_id):
        cursor.execute('''SELECT ExpiryDate, IsActive FROM subscription INNER JOIN member ON subscription.MemberID = member.MemberID WHERE subscription.MemberID = %s''', (member_id,))
        result = cursor.fetchone()
        if result and result[0] >= current_date and result[1] == 1:
            return True
        return False

    def get_staff(self, email):
        cursor.execute('''SELECT * FROM staff WHERE EmailAddress = %s''', (email,))
        return cursor.fetchone()

    def check_member(self, member_id):
        cursor.execute('''SELECT * FROM member WHERE MemberID=%s;''', (member_id,))
        return cursor.fetchone()

    

class AddMember:
    def __init__(self, email=None, first_name=None, last_name=None, dob=None, phone=None, address=None, payment_frequency=None, medical_conditions=None):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.phone = phone
        self.address = address
        self.payment_frequency = payment_frequency
        self.medical_conditions = medical_conditions

    def vallidate_phone(self, number):
        for i in number:
            if i not in '0123456789':
                return False
        return True

    def validate_email(self, email):
        cursor.execute('''SELECT EmailAddress FROM member WHERE EmailAddress = %s''', (email,))
        email_taken = cursor.fetchone()
        if email_taken:
            return False

    def validate_date(self, date):
        year_16 = datetime.now() - timedelta(days=16*365)
        date_16 = year_16.date() 
        if date > date_16:
            return False

    def add_member(self, email, first_name, last_name, dob, phone, address, payment_frequency, medical_conditions ):
        cursor.execute('INSERT INTO member (EmailAddress, FirstName, LastName, DateOfBirth, PhoneNumber, Address, PaymentFrequency, MedicalConditions, IsActive) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (email, first_name, last_name, dob, phone, address, payment_frequency, medical_conditions, 1))
        db.commit()
        new_id = cursor.lastrowid
        return new_id

    def add_subscription(self, member_id, payment_frequency):
        expiry_date = None

        if payment_frequency == 'Monthly':
            expiry_date = datetime.date(datetime.now()) + relativedelta(months=1)
            cursor.execute('INSERT INTO subscription (MemberID, StartDate, ExpiryDate, PaymentAmount, PaymentDate) VALUES (%s, CURDATE(), %s, 30, CURDATE())', (member_id, expiry_date))
        elif payment_frequency == 'Half-Yearly':
            expiry_date = datetime.date(datetime.now()) + relativedelta(months=6)
            cursor.execute('INSERT INTO subscription (MemberID, StartDate, ExpiryDate, PaymentAmount, PaymentDate) VALUES (%s, CURDATE(), %s, 150, CURDATE())', (member_id, expiry_date))
        elif payment_frequency == 'Yearly':
            expiry_date = datetime.date(datetime.now()) + relativedelta(years=1)
            cursor.execute('INSERT INTO subscription (MemberID, StartDate, ExpiryDate, PaymentAmount, PaymentDate) VALUES (%s, CURDATE(), %s, 240, CURDATE())', (member_id, expiry_date))
        db.commit()



class Admin:
    def __init__(self, staff_id=None, search=None, member_id=None, current_date=None):
        self.staff_id = staff_id
        self.member_id = member_id
        self.search = search
        self.current_date = current_date


    def get_staff_info(self, staff_id):
        query = "SELECT FirstName, LastName, StaffType FROM staff WHERE StaffID = %s"
        cursor.execute(query, (staff_id,))
        staff_info = cursor.fetchone()
        return staff_info
    
    def search_member(self, search):
        cursor.execute(
            '''SELECT m.*, s.ExpiryDate FROM member as m 
            JOIN subscription as s ON m.MemberID = s.MemberID 
            WHERE m.FirstName = %s OR m.LastName = %s OR m.MemberID = %s OR EmailAddress = %s ''', 
            (search, search, search, search,))
        return cursor.fetchall()
    
  
    def deactivate_member(self, member_id):
        cursor.execute('''UPDATE member SET IsActive = 0 WHERE MemberID = %s''', (member_id,))
        db.commit()

    def check_expiring_members(self, current_date):
        cursor.execute('''SELECT CONCAT(m.FirstName,' ',m.LastName) AS 'Member Name',
                    m.MemberID ,m.PaymentFrequency, s.ExpiryDate 
                    FROM member AS m 
                    JOIN subscription AS s ON m.MemberID = s.MemberID
                    WHERE s.ExpiryDate>=%s AND s.ExpiryDate<=DATE_ADD(%s, INTERVAL 14 DAY)
                    ORDER BY s.ExpiryDate;''',(current_date,current_date))
        results=cursor.fetchall()
        column_names=[desc[0] for desc in cursor.description]
        return results, column_names
    


class Trainer:
    def __init__(self, trainer_id=None, current_date=None, date=None, start_date=None, ending_date=None, photo_link=None):
        self.trainer_id = trainer_id
        self.current_date = current_date
        self.date  = date
        self.start_date = start_date
        self.ending_date = ending_date
        self.photo_link = photo_link

    def get_trainer_info(self, trainer_id):
        cursor.execute('''SELECT StaffID, FirstName , LastName, 
        EmailAddress, PhoneNumber, DateOfBirth, StaffType, 
        AboutMe, PhotoLink FROM staff WHERE StaffID = %s ''', (trainer_id,))
        return cursor.fetchall()
        
    def get_trainees(self, trainer_id, current_date):
        cursor.execute( ''' SELECT m.MemberID, CONCAT(m.FirstName," ", m.LastName) AS "Member Name", tt.ClassID, tt.ClassType AS "Class Name",
                            tt.ClassDate AS "Date", ts.StartTime, 
                            ts.FinishTime 
                            FROM timetable AS tt
                            JOIN timeSlots AS ts ON tt.TimeSlotsID=ts.TimeSlotsID 
                            JOIN booking as bk ON bk.ClassID = tt.ClassID
                            JOIN member as m on m.MemberID = bk.MemberID
                            AND tt.ClassType = "Private Training"
                            WHERE tt.TrainerID = %s
                            AND tt.ClassDate >=%s 
                            ORDER BY tt.ClassDate, ts.StartTime;
                            ''',(trainer_id, current_date,) )
        trainees = cursor.fetchall()
        column_names = [item[0] for item in cursor.description]
        return trainees, column_names
    
    def get_all_trainers(self):
        cursor.execute(
        '''SELECT StaffID, CONCAT(FirstName , ' ' , LastName) as Name, 
        EmailAddress, PhoneNumber, DateOfBirth, StaffType, 
        AboutMe FROM staff WHERE StaffType = "Trainer"''')
        trainers= cursor.fetchall()
        column_names = [item[0] for item in cursor.description]
        return trainers, column_names
    
    
    def get_all_trainers_schedule(self, start_date,ending_date):
        cursor.execute('''SELECT s.StaffID,CONCAT(s.FirstName,' ',s.LastName) AS Trainer,t.ClassType AS 'Class Name',
                            t.ClassDate AS Date,CONCAT(ts.StartTime, ' - ', ts.FinishTime) AS Time 
                            FROM staff AS s INNER JOIN timetable AS t 
                            ON s.StaffID = t.TrainerID 
                            INNER JOIN timeSlots AS ts ON ts.TimeSlotsID=t.TimeSlotsID
                            WHERE t.ClassDate>=%s and t.ClassDate<=%s 
                            ORDER BY s.FirstName,t.ClassDate,ts.StartTime;''',(start_date,ending_date))
        results=cursor.fetchall()
        column_names=[desc[0] for desc in cursor.description]
        return results, column_names

    def get_trainer_schedule(self, trainer, start_date,ending_date):
        cursor.execute('''SELECT s.StaffID,CONCAT(s.FirstName,' ',s.LastName) AS Trainer,t.ClassType AS 'Class Name',
                        t.ClassDate AS Date,CONCAT(ts.StartTime, ' - ', ts.FinishTime) AS Time FROM staff AS s 
                        INNER JOIN timetable AS t ON s.StaffID = t.TrainerID INNER JOIN timeSlots AS ts 
                        ON ts.TimeSlotsID=t.TimeSlotsID 
                        WHERE CONCAT(s.FirstName,' ',s.LastName)=%s AND t.ClassDate>=%s 
                        AND t.ClassDate<=%s ORDER BY t.ClassDate,ts.StartTime;''',(trainer,start_date,ending_date))
        results=cursor.fetchall()
        column_names=[desc[0] for desc in cursor.description]
        return results, column_names


    def get_class_schedule(self, trainer_id, current_date):
        cursor.execute('''SELECT tt.ClassID, tt.ClassType AS "Class Name", 
                        tt.ClassDate AS "Date", ts.StartTime, 
                        ts.FinishTime 
                        FROM timetable AS tt
                        INNER JOIN timeSlots AS ts ON tt.TimeSlotsID=ts.TimeSlotsID 
                        WHERE tt.TrainerID=%s
                        AND tt.ClassType NOT LIKE "Private Training"
                        AND tt.ClassDate >=%s AND tt.ClassDate<=DATE_ADD(%s, INTERVAL 13 DAY) 
                        ORDER BY tt.ClassDate, ts.StartTime;''',(trainer_id, current_date,current_date,) )
        class_schedule = cursor.fetchall()
        return class_schedule
    
    def get_private_schedule(self, trainer_id, current_date):
        cursor.execute( ''' SELECT tt.ClassID, tt.ClassType AS "Class Name", 
                tt.ClassDate AS "Date", ts.StartTime, 
                ts.FinishTime 
                FROM timetable AS tt
                INNER JOIN timeSlots AS ts ON tt.TimeSlotsID=ts.TimeSlotsID 
                WHERE tt.TrainerID=%s
                AND tt.ClassType ="Private Training"
                AND tt.ClassDate >=%s AND tt.ClassDate<=DATE_ADD(%s, INTERVAL 13 DAY) 
                ORDER BY tt.ClassDate, ts.StartTime;''', (trainer_id, current_date, current_date,))
        private_schedule = cursor.fetchall()
        return private_schedule
    
    def edit_trainer_info(self,firstname, lastname, phone, dob, about_me, photo_link, trainer_id ):
        cursor.execute( ''' UPDATE staff SET FirstName = %s, LastName = %s, PhoneNumber = %s, 
                        DateOfBirth = %s, AboutMe = %s , PhotoLink = %s
                        WHERE StaffID = %s''', (firstname, lastname, phone, dob,  about_me, photo_link,trainer_id))
        db.commit()

    def get_available_slots(self, trainer_id, date):
        cursor.execute('''SELECT timeSlots.TimeSlotsID , CONCAT(timeSlots.StartTime,'-',timeSlots.FinishTime) 
                                AS 'Available' from timeSlots 
                                WHERE timeSlots.TimeSlotsID 
                                NOT IN 
                                (SELECT timetable.TimeSlotsID FROM timetable 
                                WHERE timetable.TrainerID=%s AND ClassDate=%s); ''', (trainer_id, date))
        return  cursor.fetchall()
    



class Member:
    def __init__(self, member_id=None, trainer_id=None, date=None, time_slot=None, current_date=None, 
                 payment_frequency=None, phone=None, address=None, health_condition=None, 
                 firstname = None, lastname= None, dob= None, email= None):
        self.member_id = member_id
        self.trainer_id = trainer_id
        self.date = date
        self.time_slot = time_slot
        self.current_date = current_date
        self.payment_frequency = payment_frequency
        self.phone = phone
        self.address = address
        self.health_condition = health_condition
        self.firstname = firstname
        self.lastname = lastname
        self.dob = dob
        self.email = email
        
    
    def get_member_info(self, member_id):
        cursor.execute(
        '''SELECT m.*, s.ExpiryDate FROM member as m 
            JOIN subscription as s ON m.MemberID = s.MemberID
            WHERE m.MemberID = %s''', (member_id,))
        return cursor.fetchall()
    
    def update_member_info(self, payment_frequency, phone, address, health_condition, member_id):
        cursor.execute(
            '''UPDATE member SET PaymentFrequency=%s, PhoneNumber = %s, Address = %s, MedicalConditions = %s WHERE MemberID = %s''',
              (payment_frequency, phone, address, health_condition, member_id,))
        db.commit()

    def admin_edit_member(self,firstname, lastname, dob, payment_frequecy, phone, address, health_condition,email, member_id ):
        cursor.execute(
            '''UPDATE member SET FirstName = %s, LastName = %s, DateOfBirth = %s, 
            PaymentFrequency = %s, PhoneNumber = %s, Address = %s, MedicalConditions = %s, EmailAddress = %s 
            WHERE MemberID = %s''', 
            (firstname, lastname, dob, payment_frequecy, phone, address, health_condition,email, member_id, ))
        db.commit()
        
    
    def check_membership_expiry(self, member_id):
        # calculate the 15 days from today
        estimated_expiry = current_date + timedelta(days=15)
        cursor.execute(
        '''SELECT ExpiryDate FROM subscription WHERE MemberID = %s AND ExpiryDate < %s''', (member_id, estimated_expiry,))
        return  cursor.fetchone()
    
    def get_payment_date(self, member_id):
        cursor.execute(
            '''SELECT ExpiryDate FROM subscription WHERE MemberID = %s ;''', (member_id,))
        return cursor.fetchone()[0]
        
    def renew_subscription(self, expiry_date, payment_amount , member_id):
        cursor.execute(
            '''UPDATE subscription SET ExpiryDate=%s , PaymentAmount=%s  WHERE MemberID = %s''',
            (expiry_date, payment_amount , member_id,))
        db.commit()

    def get_payment_frequency(self):
        cursor.execute('''SELECT PaymentFrequency FROM paymentFrequency;''')
        return  cursor.fetchall()
    
    def book_session(self, trainer_id, date, time_slot, member_id, current_date):
        cursor.execute('''INSERT INTO timetable (ClassType, TrainerID, WeekNum, ClassDate, TimeSlotsID, Duration) 
        VALUES (%s, %s, %s, %s, %s, %s)''', ('Private Training', trainer_id, 1, date, time_slot, 1))
        db.commit()
        cursor.execute('''INSERT INTO booking (ClassID, MemberID, PaymentAmount, PaymentDate, IsPaid, HasAttended ) 
        VALUES ( %s, %s, %s, %s, %s, %s)''', (cursor.lastrowid, member_id, 35, current_date, 1, 0      ))
        db.commit()

    def chosen_trainer(self, trainer_id):
        cursor.execute(''' SELECT CONCAT(FirstName," ", LastName) as Trainer_name FROM staff WHERE StaffID = %s;''',(trainer_id,))
        return cursor.fetchone()[0]
        
    def chosen_time(self, time_slot):
        cursor.execute('''SELECT CONCAT(timeSlots.StartTime,'-',timeSlots.FinishTime) AS 'Available' from timeSlots 
        WHERE timeSlots.TimeSlotsID = %s;''', (time_slot,))
        return cursor.fetchone()[0]
    
    def get_member_booking(self, member_id, current_date):
        cursor.execute('''SELECT bk.ClassID, bk.MemberID,  tt.ClassType AS "Class Name",
                        tt.ClassDate AS "Date",
                        CONCAT( s. FirstName, " ", s.LastName ) AS  "Trainer",
                        ct.Room, ts.StartTIme, 
                        ts.FinishTime from timetable as tt
                        JOIN timeSlots as ts ON tt.TimeSlotsID=ts.TimeSlotsID 
                        JOIN booking as bk ON bk.ClassID=tt.ClassID 
                        JOIN staff as s ON tt.TrainerID = s.StaffID
                        JOIN classType ct ON ct.ClassType = tt.ClassType
                        WHERE  tt.ClassDate >=%s
                        AND bk.MemberID= %s;''' ,(current_date, member_id,))       
        return cursor.fetchall()
    
        
    
    def check_attendance(self, current_date, member_id):
        cursor.execute(
         '''SELECT bk.MemberID,CONCAT(m.FirstName, " ", m.LastName) AS "Member Name", tt.ClassID,tt.ClassDate,tt.ClassType AS "Class Name",
        CONCAT( s. FirstName, " ", s.LastName ) AS  "Trainer Name",
        CONCAT(ts.StartTime, "-", ts.FinishTime) AS "Time",bk.HasAttended 
        FROM booking as bk
        INNER JOIN member as m ON bk.MemberID=m.MemberID 
        INNER JOIN timetable  as tt ON tt.ClassID=bk.ClassID 
        INNER JOIN timeSlots as ts ON tt.TimeSlotsID=ts.TimeSlotsID 
        JOIN staff AS s ON tt.TrainerID = s.StaffID
        WHERE tt.ClassDate < %s AND m.MemberID= %s
        ORDER BY tt.ClassDate, ts.StartTime;''', (current_date, member_id,))      
        return cursor.fetchall()
    
    def cancel_booking(self, class_id, member_id):
        
        if member_id == 'Private Training':
            # delete booking information from booking table
            cursor.execute(
                '''DELETE FROM booking WHERE ClassID = %s;''', (class_id,))       
            # delete record from timetable table
            cursor.execute(
                '''DELETE FROM timetable WHERE ClassID = %s;''', (class_id,))
            db.commit()
        else:
            # delete booking information from booking table
            cursor.execute(
                '''DELETE FROM booking WHERE MemberID = %s AND ClassID = %s;''', (member_id, class_id))
            db.commit()



class GroupClass:
    def __init__(self, current_date=None, trainer_id=None, date=None, time_slot=None, 
                 class_type=None,class_id=None, member_id=None,  ):
        self.current_date = current_date
        self.trainer_id = trainer_id
        self.date = date
        self.time_slot = time_slot
        self.class_type = class_type
        self.class_id = class_id
        self.member_id = member_id


    def get_group_classes(self, current_date):
        cursor.execute(
        '''SELECT * FROM
            (SELECT tt.ClassID, tt.ClassType AS "Class Name", 
            tt.TrainerID, CONCAT(st.FirstName, " ", st.LastName) AS "Trainer",
            tt.ClassDate AS "Date", ts.StartTime, ts.FinishTime, tt.TimeSlotsID
            FROM timetable AS tt
            JOIN timeSlots AS ts ON tt.TimeSlotsID=ts.TimeSlotsID 
            JOIN staff AS st ON tt.TrainerID=st.StaffID
            WHERE tt.ClassType <> "Private Training"
            AND tt.ClassDate >=%s AND tt.ClassDate<=DATE_ADD(%s, INTERVAL 13 DAY) 
            ORDER BY tt.ClassDate, ts.StartTime) AS gs
            LEFT OUTER JOIN ( 
            SELECT tt.ClassID AS classid, COUNT(bk.MemberID) AS BookedSlots
            FROM timetable as tt
            JOIN booking as bk on bk.ClassID = tt.ClassID
            GROUP BY tt.ClassID
            ) AS booked ON  gs.ClassID = booked.ClassID;''', (current_date, current_date,))
        
        return cursor.fetchall()
    
    def check_booked_class(self, class_id, member_id):
        cursor.execute(''' Select * from booking where ClassID = %s and MemberID = %s;''', (class_id, member_id,))
        return cursor.fetchall()
    
    def book_class(self, class_id, member_id, current_date):
        cursor.execute(
                '''INSERT INTO booking (ClassID, MemberID,  PaymentAmount, 
                PaymentDate, IsPaid, HasAttended) VALUES (%s, %s, %s, %s, %s, %s   );''',
                (class_id, member_id,  0, current_date, 1, 0))
        db.commit()

    def check_slot(self, member_id, date, time_slot):
        cursor.execute('''SELECT b.MemberID, b.ClassID, t.ClassDate, t.TimeSlotsID
                        FROM booking as b
                        inner JOIN timetable AS t 
                        ON t.ClassID = b.ClassID
                        WHERE b.MemberID = %s
                        AND t.ClassDate = %s
                        AND t.TimeSlotsID =%s;''', (member_id, date, time_slot))
        return cursor.fetchone()    



class Report:
    def __init__(self, starting_date=None, ending_date=None, type_of_visit=None, start_date=None):
        self.starting_date = starting_date
        self.ending_date = ending_date
        self.type_of_visit = type_of_visit
        self.start_date = start_date
        
        
    def attendance_report(self, starting_date, ending_date):
        # query attendance record by selected search criteria.
        cursor.execute('''SELECT a.TypeOfVisit AS 'Type Of Visit',a.Date,CONCAT(m.FirstName,' ',m.LastName)
        AS 'Member Name',a.CheckinTime AS 'Checkin Time' FROM attendance AS a 
        INNER JOIN member AS m ON a.MemberID=m.MemberID WHERE a.Date>=%s AND
        a.Date<=%s  ORDER BY a.Date,
        a.CheckinTime;''',(starting_date,ending_date,))
        attendance_records=cursor.fetchall()
        column_names=[desc[0] for desc in cursor.description]
        return attendance_records,column_names
    
    def attendance_number(self, starting_date, ending_date):
        # query total number of attendance.
        cursor.execute('''SELECT a.TypeOfVisit,a.Date, COUNT(m.FirstName) as Numeber
                FROM attendance AS a INNER JOIN member AS m ON a.MemberID=m.MemberID
                WHERE a.Date>= %s AND a.Date<= %s  
                GROUP BY a.Date, a.TypeOfVisit;''',(starting_date,ending_date,))
        return cursor.fetchall()
    
    def total_visits(self, starting_date, ending_date):
        # query total number of visits.
        cursor.execute('''SELECT COUNT(MemberID) FROM attendance AS a WHERE a.Date>=%s AND\
        a.Date<=%s ;''',(starting_date,ending_date,))
        return cursor.fetchone()
    
    def pt_revenue_report(self, start_date, ending_date):
        cursor.execute('''
            SELECT "Personal Training " AS "Income Type", COUNT(booking.ClassID) AS 'Number',
                SUM(booking.PaymentAmount) AS 'Revenue' 
                FROM booking WHERE PaymentDate>=%s AND PaymentDate<=%s 
                AND IsPaid=1 
                AND booking.PaymentAmount<>0;''',(start_date,ending_date,))
        return cursor.fetchall()
        
        
    
    def subscription_revenue_report(self, start_date, ending_date):
        cursor.execute('''SELECT CONCAT( member.PaymentFrequency," Subscription" )AS "Income Type",
                                COUNT(ss.SubscriptionID)AS 'Number',
                                SUM(ss.PaymentAmount) AS Revenue 
                                FROM member 
                                INNER JOIN subscription as ss ON member.MemberID=ss.MemberID 
                                WHERE ss.PaymentDate>=%s AND ss.PaymentDate<=%s 
                                GROUP BY member.PaymentFrequency''',(start_date,ending_date,))
        revenue=cursor.fetchall()
        
        cursor.execute('''SELECT SUM(Revenue) FROM (
                        SELECT CONCAT( member.PaymentFrequency," Subscription" )AS Income_type,
                        COUNT(ss.SubscriptionID)AS Number,
                        SUM(ss.PaymentAmount) AS Revenue 
                        FROM member 
                        INNER JOIN subscription as ss ON member.MemberID=ss.MemberID 
                        WHERE ss.PaymentDate>=%s AND ss.PaymentDate<=%s
                        GROUP BY member.PaymentFrequency ) AS sub;''',(start_date,ending_date,))
        total_revenue=cursor.fetchone()
        total_revenue = total_revenue[0]
        return revenue,total_revenue
    
    def total_revenue_report(self, start_date, ending_date):
        cursor.execute('''SELECT CONCAT( member.PaymentFrequency," Subscription" )AS "Income Type",
                                COUNT(ss.SubscriptionID)AS 'Number',
                                SUM(ss.PaymentAmount) AS Revenue 
                                FROM member 
                                INNER JOIN subscription as ss ON member.MemberID=ss.MemberID 
                                WHERE ss.PaymentDate>=%s AND ss.PaymentDate<=%s
                                GROUP BY member.PaymentFrequency
                                UNION
                                SELECT "Personal Training " AS "Income Type", COUNT(booking.ClassID) AS 'Number',
                                SUM(booking.PaymentAmount) AS 'Revenue' 
                                FROM booking WHERE PaymentDate>=%s AND PaymentDate<=%s 
                                AND IsPaid=1 
                                AND booking.PaymentAmount<>0;''',(start_date,ending_date,start_date,ending_date, ))
        revenue=cursor.fetchall()
        cursor.execute('''SELECT SUM(Revenue) FROM (
                                SELECT CONCAT( member.PaymentFrequency," Subscription" )AS "Income Type",
                                COUNT(ss.SubscriptionID)AS 'Number',
                                SUM(ss.PaymentAmount) AS Revenue 
                                FROM member 
                                INNER JOIN subscription as ss ON member.MemberID=ss.MemberID 
                                WHERE ss.PaymentDate>=%s AND ss.PaymentDate<=%s
                                GROUP BY member.PaymentFrequency
                                UNION
                                SELECT "Personal Training " AS "Income Type", COUNT(booking.ClassID) AS 'Number',
                                SUM(booking.PaymentAmount) AS 'Revenue' 
                                FROM booking WHERE PaymentDate>=%s AND PaymentDate<=%s 
                                AND IsPaid=1 
                                AND booking.PaymentAmount<>0) AS total;''' ,(start_date,ending_date, start_date,ending_date))
        total_revenue=cursor.fetchone()
        total_revenue = total_revenue[0]
        return revenue,total_revenue
    
    def class_ranking(self, start_date, ending_date):
        # Query the database for class ranking.
        cursor.execute('''SELECT timetable.ClassType AS 'Class Name',COUNT(booking.MemberID) AS 'Total Attendance',\
        DENSE_RANK() OVER(ORDER BY COUNT(MemberID) DESC) AS Ranking FROM booking INNER JOIN timetable\
        ON timetable.ClassID=booking.ClassID WHERE timetable.ClassDate>=%s AND timetable.ClassDate<=%s\
        AND timetable.ClassType <> 'Private Training'
        GROUP BY timetable.ClassType ORDER BY COUNT(MemberID) DESC;''',(start_date,ending_date,))
        results=cursor.fetchall()
        column_names=[desc[0] for desc in cursor.description]
        return results, column_names


class Attendance:
    def __init__(self, member_id=None, time_now=None, class_id=None, current_date=None, checkin_time=None, checkout_time=None, type_of_visit=None ):
        self.member_id = member_id
        self.class_id = class_id
        self.checkin_time = checkin_time
        self.current_date=  current_date
        self.time_now = time_now
        self.checkout_time = checkout_time
        self.type_of_visit = type_of_visit


    def get_upcoming_booking(self,time_now, member_id):
        # Query the database for upcoming classes.
        cursor.execute('''SELECT timetable.ClassID,timetable.ClassType AS Class,\
                            timeSlots.StartTime,timeSlots.FinishTime FROM booking INNER JOIN member \
                            ON booking.MemberID=member.MemberID INNER JOIN timetable ON timetable.ClassID=booking.ClassID \
                            INNER JOIN timeSlots ON timetable.TimeSlotsID=timeSlots.TimeSlotsID\
                            WHERE CAST(CONCAT(timetable.ClassDate, ' ', timeSlots.StartTime) as datetime)>=%s\
                            AND CAST(CONCAT(timetable.ClassDate, ' ', timeSlots.StartTime) as datetime)<ADDTIME(%s,'01:00:00')\
                            AND member.MemberID=%s ORDER BY timeSlots.StartTime;''',(time_now,time_now,member_id))
        return cursor.fetchall()
    
    def update_booking_attended(self,class_id, member_id):
        # update booking as attended
        cursor.execute('''UPDATE booking SET HasAttended=1 WHERE ClassID=%s AND MemberID=%s''',(class_id, member_id,))
        db.commit()
        

    def general_checkin(self, member_id, type_of_visit, current_date, checkin_time):
        cursor.execute('''INSERT INTO attendance (MemberID, TypeOfVisit, Date, CheckinTime) VALUES (%s, %s, %s, %s);''', (member_id, type_of_visit, current_date, checkin_time, ))
        db.commit()
            # update member's checkin status
        cursor.execute("UPDATE member SET Checkin=1 WHERE MemberID=%s;", (member_id,))
        db.commit()

    def member_checkout(self,current_date,checkout_time,member_id):
        # get the attendance id of the member
        cursor.execute('''SELECT MAX(AttendanceID) FROM attendance WHERE Date=%s\
        AND MemberID=%s AND CheckinTime IS NOT NULL AND CheckoutTime IS NULL;''', (current_date,member_id,))
        attendance_id = cursor.fetchall()[0][0]
        # update checkout time
        cursor.execute("UPDATE attendance SET CheckoutTime=%s WHERE AttendanceID=%s;", (checkout_time, attendance_id,))
        db.commit()
        # update member checkin status as 0 false
        cursor.execute("UPDATE member SET Checkin=0 WHERE MemberID=%s;", (member_id,))
        db.commit()
                    
class News:
    def __init__(self,  staff_id=None ,title=None, content=None, date=None, news_id=None):
        self.title = title
        self.content = content
        self.date = date
        self.staff_id = staff_id
        self.news_id = news_id

    def get_all_news(self):
        # Query the database for news.
        # Display latest news first.
        cursor.execute('''SELECT * FROM news ORDER BY Date DESC''')
        return cursor.fetchall()
        
    def add_news(self, staff_id, title, content, date):
        # Add news to database.
        cursor.execute(
                '''INSERT INTO news (StaffID, Subject, Content, Date) VALUES (%s, %s, %s, %s)''', (staff_id, title, content, date, ))
        db.commit()

    def get_news(self, news_id):
        # Query the database for news.
        cursor.execute('''SELECT * FROM news WHERE NewsID=%s''', (news_id,))
        return cursor.fetchone()
    
    def edit_news(self, staff_id, title, content, date, news_id):
        # Edit news in database.
        cursor.execute(
                '''UPDATE news SET StaffID=%s, Subject=%s, Content=%s, Date=%s 
                WHERE NewsID=%s''', (staff_id, title, content, date, news_id, ))
        db.commit()
        return True

    def delete_news(self, news_id):
        # Delete news in database.
        cursor.execute('''DELETE FROM news WHERE NewsID=%s''', (news_id,))
        db.commit()
        


    

    
    
    


