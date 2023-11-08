## Contributors -- comp693-2023-project1-group26


** Carol Song  /  Gavin Wang  /  Heather Wang  /  Jason Tang **


## Features
*You can test the system by using*  
Manager: John@lincolnfitness.co.nz
Trainer: Sarah@lincolnfitness.co.nz
Admin: Li@lincolnfitness.co.nz
Member: Eve.Miller@gmail.com

Lincoln Fitness is a gym with 1000 members and 10 personal trainers, and they are looking to automate their current manual system for managing members and trainers. This system will keep track of the members' subscription payments, their usage of the gym, and allow members to book exercise sessions with personal trainers.

There are three types of users: Admin/Manager, Member, and Trainer. The system will store members’ information and keep track of their training and monthly subscription payments

Members can log in to the system to update their profile and book training sessions with personal trainers

Trainers can use the system to offer specialised training and view their trainees' information. Members are required to pay additional fees for each specialised training.

The fitness centre runs exercise classes for its members, and each class can accommodate a maximum of 30 members. Members can book classes ahead of time to secure their places.

When a member arrives at the gym, they will scan their member's card to record their attendance. The system will determine if the member is attending a training session, a class, or just using the gym.



### Admin/Manager

Search member by member ID or first name

Manage member details by adding, updating, and deactivating

View member's attendance

View member's subscription status

View list of expiring membrship

View trainer’s classes

Generate financial report for the club

View popular classes

Sends reminders to members when their subscription is due

Sends news/updates on the website


### Member

Track attendance by checkin and checkout

View and update profile

View personal attendance record

View booked sessions and group classes

View list of trainers 

Book a session with a trainer

Make a payment for personal session

View next 14 days of group class schedule

Book an exercise class

Renew membership subscription


### Trainer

View and update profile

View trainee's information

View upcoming group class schedule

View upcoming personal session schedule

Cancel personal session


## How to Run

All the wtforms are located in webforms.py

Mysql queries was moved to model.py

Navigate to your current project directory for this case it will be comp693-2023-project1-group26.

### 1 .Fork the repository and Clone it into your local machine

```
gh repo clone LUMasterOfAppliedComputing/comp693-2023-project1-group26
```

### 2 .Create an environment
Check to make sure you are in the same directory where you did the git clone,if not navigate to that specific directory.

Depending on your operating system,make a virtual environment to avoid messing with your machine's primary dependencies

Windows

```
cd comp693-2023-project1-group26
py -3 -m venv venv
```

macOS/Linux

```
cd comp693-2023-project1-group26
python3 -m venv venv
```

### 3 .Activate the environment
Windows

```
venv\Scripts\activate
```

macOS/Linux

```
. venv/bin/activate or source venv/bin/activate
```

### 4 .Install the requirements

Applies for windows/macOS/Linux

```
pip install -r requirements.txt
```

### 5 .Run the application
Run python app.py in your terminal
Open your browser and go to http://localhost:5000

## Technologies Used
Python
Flask
HTML
CSS
Bootstrap
MySQL
JavaScript



