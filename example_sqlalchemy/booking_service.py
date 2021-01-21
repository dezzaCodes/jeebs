from datetime import date, datetime, timedelta
from flask_mail import Message

from main import db, mail
from main.model.clinic_exam_types import ClinicExamType
from main.model.examination import Examination
from main.model.booking import Booking
from main.model.clinic import Clinic
from main.model.user import User
from main.model.employee import Employee
from main.model.opening_hours import OpeningHours
from main.model.question import Question
from main.model.alternative import Alternative
from flask import g

from collections import OrderedDict
import copy

def save_new_patient_and_booking(data):
    if booking_available(data):
        user = User.query.filter_by(email=data['email']).first()
        print("user is", user)
        if not user:
            dob_data = data['dob'].split("/")
            dob = date(int(dob_data[2]), int(dob_data[1]), int(dob_data[0]))

            #  Create a new new
            user  = User(
                first_name=data['first name'],
                last_name=data['last name'],
                email=data['email'],
                phone=data['phone'],
                dob=dob,
                gender=data['gender'],             
                password=data['password'],
                street=data['address'],
                suburb=data['suburb'],
                state=data['state'],
                postcode=data['postcode']
            )

            db.session.add(user)

            user_id = db.session.query(db.func.max(User.id)).scalar()
            booking_outcome = save_new_booking(data, user_id)

            return booking_outcome
        else:
            response_object = {
                'status': 'fail',
                'message': 'User already registered. Please log in.'
            }
            return response_object, 409

def save_new_booking(data, user_id):
    print("Save new booking", data, user_id)
    if booking_available(data):
        try:
            date_data = data['date'].split("/")
            time_data = data['time'].split(":")
            date_time = datetime(int(date_data[2]), int(date_data[1]), int(date_data[0]), int(time_data[0]), int(time_data[1]))

            # Get corresponding clinic
            clinic = Clinic.query.filter_by(name=data['clinic']).first()
            exam = Examination.query.filter_by(name=data['exam']).first()
            booking = Booking(
                date_time=date_time,
                clinic_id=clinic.id,
                examination_id=exam.id,
                user_id=user_id
            )
            print("Save new booking, booking is",booking)
            db.session.add(booking)
            send_request_email(booking)

            db.session.commit()
            response_object = {
                    'status': 'success',
                    'message': 'Successfully created new booking.'
                }
            return response_object, 201
        except:
            db.session.rollback()
            response_object = {
                'status': 'fail',
                'message': 'Booking did not go through'
            }
            return response_object, 500
    else:
        response_object = {
            'status': 'fail',
            'message': 'Please try another appointment time.',
        }
        return response_object, 409

def update_booking(data):
    booking = Booking.query.filter_by(id=data['id']).first()
    if booking:
        date_data = data['date'].split("/")
        time_data = data['time'].split(":")
        date_time = datetime(int(date_data[2]), int(date_data[1]), int(date_data[0]), int(time_data[0]), int(time_data[1]))


        clinic = Clinic.query.filter_by(name=data['clinic']).first()
        examination = Examination.query.filter_by(name=data['exam']).first()

        old_date_time = booking.date_time
        old_clinic_id = booking.clinic_id
        old_examination_id = booking.examination_id
        old_confirmed = booking.confirmed
        old_user_id = booking.user_id

        # TODO Update the assigned radiologist
        # booking.radiologist_id=booking.radiologist_id

        # Patient update
        if not data['admin']:
            # If exam type or clinic is changed then a new booking request is made and the 
            # old booking is cancelled.
            if examination.id != old_examination_id or clinic.id != old_clinic_id:
                delete_booking(booking.id)
                db.session.commit()
                save_new_booking(data, old_user_id)
            # If only date or time change then a request for updated booking time is sent
            # to the relevant clinic.
            else:
                booking.date_time=date_time
                booking.confirmed = False
                db.session.commit()
                
                # Check if the update was an alternative suggested by clinic
                alternatives = Alternative.query.filter_by(booking_id=booking.id, date_time=date_time).first()
                if alternatives:
                    booking.confirmed = True
                    db.session.commit()
                    send_alternative_confirmed(booking)
                else:
                    old_booking = Booking(date_time=old_date_time, clinic_id=old_clinic_id, examination_id=old_examination_id, user_id=old_user_id)
                    send_updated_request_email(booking, old_booking)
        # Admin update
        else:
            # If the change is booking time has been confirmed the send patient 
            # confirmation email.
            booking.confirmed=data['confirmed']
            db.session.commit()
            if booking.confirmed and not old_confirmed:
                send_patient_confirmed_email(booking)

        response_object = {
                'status': 'success',
                'message': 'Successfully updated booking.'
            }
        return response_object, 201
    else:
        response_object = {
            'status': 'fail',
            'message': 'Booking was not found',
        }
    return response_object, 404

def update_booking_user(data):
    booking = Booking.query.filter_by(id=data['id']).first()
    if booking:
        date_data = data['date'].split("/")
        time_data = data['time'].split(":")
        date_time = datetime(int(date_data[2]), int(date_data[1]), int(date_data[0]), int(time_data[0]), int(time_data[1]))

        # duplicate the booking
        old_booking = copy.deepcopy(booking)
        booking.date_time=date_time
        booking.confirmed = False
        db.session.commit()
                
        # Check if the update was an alternative suggested by clinic
        alternatives = Alternative.query.filter_by(booking_id=booking.id, date_time=date_time).first()
        if alternatives:
            booking.confirmed = True
            # delete the alternatives for this booking
            for alternative in Alternative.query.filter_by(booking_id=booking.id).all():
                db.session.delete(alternative)

            db.session.commit()
            send_alternative_confirmed(booking)
        else:
            # old_booking = Booking(date_time=old_date_time, clinic_id=old_clinic_id, examination_id=old_examination_id, user_id=old_user_id)
            # send email to clinic with details of old and new booking
            send_updated_request_email(booking, old_booking)

        response_object = {
                'status': 'success',
                'message': 'Successfully updated booking.'
            }
        return response_object, 201
    else:
        response_object = {
            'status': 'fail',
            'message': 'Booking was not found',
        }
    return response_object, 404

# a function to update the booking from the admin
def update_booking_admin(id, data):
    current_employee = g.current_employee
    clinic = current_employee.clinic
    booking = Booking.query.filter_by(id=id).first()
    # check if this admin has authority to this booking
    if booking.clinic != clinic:
        response_object = {
                'status': 'fail',
                'message': 'Unauthorized action.'
            }
        return response_object, 401
    # confirm the booking
    if 'confirmed' in data:
        booking.confirmed=data['confirmed']
        db.session.commit()
        send_patient_confirmed_email(booking)
        response_object = {
            'status': 'success',
            'message': 'Successfully updated booking.'
        }
        return response_object, 201

    elif 'date' in data and 'time' in data:
        date_data = data['date'].split("/")
        time_data = data['time'].split(":")
        date_time = datetime(int(date_data[2]), int(date_data[1]), int(date_data[0]), int(time_data[0]), int(time_data[1]))
        booking.confirmed = True
        booking.date_time = date_time
        db.session.commit()
        send_patient_confirmed_email(booking)
        response_object = {
            'status': 'success',
            'message': 'Successfully updated booking.'
        }
        return response_object, 201


def get_a_booking(id):
    booking = Booking.query.filter_by(id=id).first()
    if booking:
        # Trung updated to get more details
        print(format_booking_for_user(booking))
        return format_booking_for_user(booking)
    else:
        return None

def get_all_bookings():
    info = [format_booking(booking) for booking in Booking.query.all()]
    return info

def get_bookings_by_clinic(clinic_id, confirmed, fromDate, duration):
    if not confirmed or confirmed == 'false':
        info = [format_booking(booking) for booking in Booking.query.filter_by(clinic_id=clinic_id).all()]
        return info
    elif confirmed == 'true':
        date_data = fromDate.split("/")
        from_date = datetime(int(date_data[2]), int(date_data[1]), int(date_data[0]))
        to_date = from_date + timedelta(days=duration)  
        bookings = Booking.query.filter(Booking.clinic_id==clinic_id, Booking.confirmed==True, Booking.date_time > from_date, Booking.date_time <= to_date).order_by(Booking.date_time).all()
        # print(bookings)
        # Return the booking in a dictionary format
        booking_dict = OrderedDict()
        for booking in bookings:
            booking_date = booking.date_time.date().strftime("%d/%m/%Y")
            if booking_date not in booking_dict:
                booking_dict[booking_date] = [format_booking(booking)]
            else:
                booking_dict[booking_date].append(format_booking(booking))

        print(booking_dict)
        return booking_dict

def get_user_bookings(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        response_object = {
            'status': 'fail',
            'message': 'User does not exit.',
        }
        return response_object, 404

    bookings = Booking.query.filter_by(user_id=user_id).all()
    info = [format_booking(booking) for booking in bookings]
    return info


def format_booking(booking):
    questions = Question.query.filter_by(booking_id=booking.id).all()
    list_of_questions = [format_question(q) for q in questions]
    alternatives = Alternative.query.filter_by(booking_id=booking.id).all()
    list_of_alternatives = []
    for alternative in alternatives:
        formatted = {
            'booking id': alternative.booking_id,
            'date': alternative.date_time.strftime("%d/%m/%Y"),
            'time': alternative.date_time.strftime("%H:%M")
        }
        list_of_alternatives.append(formatted) 

    return {
            'user id': booking.user_id,
            'id': booking.id,
            'date': booking.date_time.date().strftime("%d/%m/%Y"),
            'time': booking.date_time.time().strftime("%H:%M"),
            'clinic': booking.clinic.name,
            'duration': booking.examination.duration,
            'firstName': booking.user.first_name,
            'lastName': booking.user.last_name,
            'exam': booking.examination.name,
            'radiologist': booking.radiologist,
            'confirmed': booking.confirmed,
            'gender': booking.user.gender,
            'dob': booking.user.dob.strftime("%d/%m/%Y"),
            'email': booking.user.email,
            'phone': booking.user.phone,
            'address': booking.user.street,
            'suburb': booking.user.suburb,
            'state': booking.user.state,
            'postcode': booking.user.postcode,
            'additional info': list_of_questions,
            'alternatives': list_of_alternatives
        }

def format_booking_for_user(booking):
    questions = Question.query.filter_by(booking_id=booking.id).all()
    list_of_questions = [format_question(q) for q in questions]
    alternatives = Alternative.query.filter_by(booking_id=booking.id).all()
    list_of_alternatives = []
    for alternative in alternatives:
        formatted = {
            'booking id': alternative.booking_id,
            'date': alternative.date_time.strftime("%d/%m/%Y"),
            'time': alternative.date_time.strftime("%H:%M")
        }
        list_of_alternatives.append(formatted) 

    return {
            'user id': booking.user_id,
            'id': booking.id,
            'date': booking.date_time.date().strftime("%d/%m/%Y"),
            'time': booking.date_time.time().strftime("%H:%M"),
            'clinic': booking.clinic.name,
            'duration': booking.examination.duration,
            'firstName': booking.user.first_name,
            'lastName': booking.user.last_name,
            'exam': booking.examination.name,
            'radiologist': booking.radiologist,
            'confirmed': booking.confirmed,
            'gender': booking.user.gender,
            'dob': booking.user.dob.strftime("%d/%m/%Y"),
            'email': booking.user.email,
            'phone': booking.user.phone,
            'address': booking.user.street,
            'suburb': booking.user.suburb,
            'state': booking.user.state,
            'postcode': booking.user.postcode,
            'additional info': list_of_questions,
            'alternatives': list_of_alternatives,
            'clinic_id': booking.clinic.id,
            'clinic_phone': booking.clinic.phone,
            'clinic_address': booking.clinic.address.street,
            'clinic_postcode': booking.clinic.address.postcode,
            'clinic_suburb': booking.clinic.address.suburb,
            'clinic_state': booking.clinic.address.state,
        }

def get_unavailable_times(clinic, exam):
    info = []
    # get all bookings
    clinic = Clinic.query.filter_by(name=clinic).first()
    if clinic:
        # get all opening hours
        opening_hours = OpeningHours.query.filter_by(clinic_id=clinic.id).all()
        for interval in opening_hours:
            timeslot = {
                'opening hours': True,
                'day': interval.day,
                'open': interval.opening_time.strftime('%H:%M'),
                'close': interval.closing_time.strftime('%H:%M')
            }
            info.append(timeslot)

        exam_id = Examination.query.filter_by(name=exam).first().id
        bookings = Booking.query.join(ClinicExamType, ClinicExamType.examination_id==Booking.examination_id).filter_by(clinic_id=clinic.id, examination_id=exam_id).all()
        for booking in bookings:
            print(booking)
            timeslot = {
                'opening hours': False,
                'start': booking.date_time,
                'end': booking.date_time + timedelta(minutes=booking.examination.duration)
            }
            info.append(timeslot)

        return info
    else:
        response_object = {
            'status': 'fail',
            'message': 'Clinic does not exist'
        }
        return response_object

def delete_booking_admin(id):
    booking = Booking.query.filter_by(id=id).first()
    if booking:
        send_cancel_booking_from_admin(booking)
    Question.query.filter_by(booking_id=id).delete()
    Alternative.query.filter_by(booking_id=id).delete()
    if Booking.query.filter_by(id=id).delete():
        db.session.commit()
        response_object = {
            'status': 'success',
            'message': 'booking has been deleted'
        }
        return response_object, 200
    
    response_object = {
        "status": 'fail',
        "message": 'Booking was not found or could not be deleted'
    }
    return response_object, 404

def delete_booking(id):
    booking = Booking.query.filter_by(id=id).first()
    if booking:
        send_cancel_booking(booking)
    Question.query.filter_by(booking_id=id).delete()
    Alternative.query.filter_by(booking_id=id).delete()
    if Booking.query.filter_by(id=id).delete():
        db.session.commit()
        response_object = {
            'status': 'success',
            'message': 'booking has been deleted'
        }
        return response_object, 200
    
    response_object = {
        "status": 'fail',
        "message": 'Booking was not found or could not be deleted'
    }
    return response_object, 404

# the function to save question from admin/clinic
def save_new_question_admin(data):
    booking = Booking.query.filter_by(id=data['booking id']).first()
    if booking is not None:
        question = Question(
            question=data['question'],
            # answer=data['answer'],
            booking_id=data['booking id']
            )
        db.session.add(question)
        db.session.commit()
        response_object = {
            'status': 'success',
            'message': 'question successfully created'
        }
        return response_object, 200
    else:
        response_object = {
            'status': 'fail',
            'message': 'booking not found'
        }
        return response_object, 404

# the function to save question from admin/clinic
def get_questions(booking):
    if booking is not None:
        questions = Question.query.filter_by(booking_id=booking.id).all()
        formated_questions = [format_question(q) for q in questions]
        return formated_questions
    else:
        response_object = {
            'status': 'fail',
            'message': 'booking not found'
        }
        return response_object, 404

# the function to save question from admin/clinic
def update_questions(bookingID, data):
    questions = Question.query.filter_by(booking_id=bookingID).all()
    for question in questions:
        for item in data:
            if question.question == item['question']:
                print("found any?")
                question.answer = item['answer'] # update the answer
                db.session.add(question)
                break
    
    db.session.commit()
    response_object = {
            'status': 'success',
            'message': 'question successfully updated'
        }
    return response_object, 200


def format_question(q):
    print("question answer", q)
    if q.answer:
        return {'question': q.question, 'answer': q.answer }
    else:
        return {'question': q.question, 'answer': ''}

def booking_available(booking):
    # TODO check if time is available
    return True

# function to store alternative times for a booking by clinic admin
def save_alternatives(bookingID, data):
    date_time_list = []
    for alt in data:
        try:
            date_data = alt['date'].split("/")
            time_data = alt['time'].split(":")
            date_time = datetime(int(date_data[2]), int(date_data[1]), int(date_data[0]), int(time_data[0]), int(time_data[1]))
            date_time_list.append(date_time)
        except:
            response_object = {
                'status': 'fail',
                'message': 'Date and time not in correct format'
            }
            return response_object, 400
    
    # check if all date+time are unique
    if len(date_time_list) != len(set(date_time_list)):
        response_object = {
                'status': 'fail',
                'message': 'Date and time not in correct format'
            }
        return response_object, 400

    
    for date_time in date_time_list:
        alternative = Alternative(booking_id=bookingID, date_time=date_time)
        db.session.add(alternative)

    db.session.commit()
    send_patient_reschedule_email(bookingID, date_time_list) #send user a notification
    response_object = {
        'status': 'success',
        'message': 'Alternatives successfully sent to patient'
    }
    return response_object, 200

def send_request_email(booking):
    print(booking)
    # function to send an email to the clinic when new request is made
    clinic = Clinic.query.filter_by(id=booking.clinic_id).first()
    patient = User.query.filter_by(id=booking.user_id).first()

    clinic_email = 'skywalkerradiology@gmail.com'
    #TODO Uncomment below if real clinic_email is used
    print("We get here?")
    admin = Employee.query.filter_by(clinic_id=booking.clinic_id).first()
    clinic_email = admin.email
    print(clinic_email)

    msg = Message("New booking request", sender="skywalkerradiology@gmail.com", recipients=[clinic_email])
    msg.body = f'Hi {clinic.name},\n\nYou have a new booking request.\n\n\tName: {patient.first_name} {patient.last_name}\n\tDate: {booking.date_time.strftime("%d/%m/%y")}\n\tTime: {booking.date_time.strftime("%H:%M")}\n\tLocation: {clinic.name}\n\tExamination: {booking.examination.name}\n\nPlease go to our website to confirm booking.\n\nKind regards,\nSkywalker Radiology'
    mail.send(msg)
    return True

def send_updated_request_email(booking, old_booking):
    clinic = Clinic.query.filter_by(id=booking.clinic_id).first()
    patient = User.query.filter_by(id=booking.user_id).first()

    clinic_email = 'skywalkerradiology@gmail.com'
    #TODO Uncomment below if real clinic_email is used
    admin = Employee.query.filter_by(clinic_id=booking.clinic_id).first()
    clinic_email = admin.email

    msg = Message("Updated booking request", sender="skywalkerradiology@gmail.com", recipients=[clinic_email])
    msg.body = f'Hi {clinic.name},\n\nYou have a request to update an existing booking.\n\nOld booking:\n\tName: {patient.first_name} {patient.last_name}\n\tDate: {old_booking.date_time.strftime("%d/%m/%y")}\n\tTime: {old_booking.date_time.strftime("%H:%M")}\n\tLocation: {clinic.name}\n\tExamination: {booking.examination.name}\n\nUpdated booking request:\n\tName: {patient.first_name} {patient.last_name}\n\tDate: {booking.date_time.strftime("%d/%m/%y")}\n\tTime: {booking.date_time.strftime("%H:%M")}\n\tLocation: {clinic.name}\n\tExamination: {booking.examination.name}\n\nPlease go to our website to confirm booking.\n\nKind regards,\nSkywalker Radiology'
    mail.send(msg)
    return True

def send_cancel_booking(booking):
    clinic = Clinic.query.filter_by(id=booking.clinic_id).first()
    patient = User.query.filter_by(id=booking.user_id).first()
   
    clinic_email = 'skywalkerradiology@gmail.com'
    #TODO Uncomment below if real clinic_email is used
    admin = Employee.query.filter_by(clinic_id=booking.clinic_id).first()
    clinic_email = admin.email

    msg = Message("Booking cancellation", sender="skywalkerradiology@gmail.com", recipients=[clinic_email])
    msg.body = f'Hi {clinic.name},\n\n{patient.first_name} {patient.last_name} has cancelled their booking through our platform. The patient has requested the following booking to be cancelled:\n\n\tName: {patient.first_name} {patient.last_name}\n\tDate: {booking.date_time.strftime("%d %B %Y")}\n\tTime: {booking.date_time.strftime("%I:%M %p")}\n\tLocation: {clinic.name}\n\tExamination: {booking.examination.name}\n\nPlease go to our website to access your bookings.\n\nKind regards,\nSkywalker Radiology'
    mail.send(msg)
    return True

def send_cancel_booking_from_admin(booking):
    clinic = Clinic.query.filter_by(id=booking.clinic_id).first()
    patient = User.query.filter_by(id=booking.user_id).first()
   
    user_email = 'skywalkerradiology@gmail.com'
    #TODO Uncomment below if real clinic_email is used
    admin = Employee.query.filter_by(clinic_id=booking.clinic_id).first()
    user_email = patient.email

    msg = Message("Booking cancellation", sender="skywalkerradiology@gmail.com", recipients=[user_email])
    msg.body = f'Hi {patient.first_name} {patient.last_name},\n\n{clinic.name} has cancelled your booking through our platform. Below is the details of the canceled booking:\n\n\tName: {patient.first_name} {patient.last_name}\n\tDate: {booking.date_time.strftime("%d %B %Y")}\n\tTime: {booking.date_time.strftime("%I:%M %p")}\n\tLocation: {clinic.name}\n\tExamination: {booking.examination.name}\n\nIf this is a mistake, please give us a call at 0432 999 999.\n\nKind regards,\nSkywalker Radiology'
    mail.send(msg)
    return True

def send_patient_confirmed_email(booking):
    patient = User.query.filter_by(id=booking.user_id).first()
    clinic = Clinic.query.filter_by(id=booking.clinic_id).first()

    patient_email = 'skywalkerradiology@gmail.com'
    # TODO Uncomment below if real patient_email is used
    patient_email = patient.email

    msg = Message("Booking Confirmation", sender="skywalkerradiology@gmail.com", recipients=[patient_email])
    msg.body = f'Hi {patient.first_name} {patient.last_name},\n\nYour booking has been confirmed.\n\nDetails:\n\tDate: {booking.date_time.strftime("%d/%m/%y")}\n\tTime: {booking.date_time.strftime("%H:%M")}\n\tLocation: {clinic.name}\n\tExamination: {booking.examination.name}\n\nTo reschedule or cancel your booking please go to our website\n\nKind regards,\nSkywalker Radiology'
    mail.send(msg)
    return True

def send_patient_reschedule_email(bookingID, date_time_list):
    # print(booking_list[0])
    booking = Booking.query.filter_by(id=bookingID).first()
    patient = booking.user
    clinic = booking.clinic

    patient_email = 'skywalkerradiology@gmail.com'
    # TODO Uncomment below if real patient_email is used
    patient_email = patient.email

    body = f'Hi {patient.first_name} {patient.last_name},\n\nUnfortunately the requested time for your {booking.examination} examination is unavailable.\n\nSuggested alternatives:'
    for date_time in date_time_list:
        body += f'\n\n\tDate: {date_time.strftime("%A %d %B %Y")}\n\tTime: {date_time.strftime("%I:%M %p")}\n\tLocation: {clinic.name}'
    body += f'\n\nTo select an alternative time please go to our webiste\n\nKind regards,\nSkywalker Radiology'
    msg = Message("Alternative dates for your booking", sender="skywalkerradiology@gmail.com", recipients=[patient_email])
    msg.body = body 
    mail.send(msg)
    return True

def send_alternative_confirmed(booking):
    clinic = Clinic.query.filter_by(id=booking.clinic_id).first()
    patient = User.query.filter_by(id=booking.user_id).first()
   
    clinic_email = 'skywalkerradiology@gmail.com'
    #TODO Uncomment below if real clinic_email is used
    admin = Employee.query.filter_by(clinic_id=booking.clinic_id).first()
    clinic_email = admin.email

    msg = Message("Alternative Booking Confirmed By Patient", sender="skywalkerradiology@gmail.com", recipients=[clinic_email])
    msg.body = f'Hi {clinic.name},\n\n{patient.first_name} {patient.last_name} has confirmed the alternative date and time you suggested through our platform. The booking details are as follows:\n\n\tName: {patient.first_name} {patient.last_name}\n\tDate: {booking.date_time.strftime("%d/%m/%y")}\n\tTime: {booking.date_time.strftime("%H:%M")}\n\tLocation: {clinic.name}\n\tExamination: {booking.examination.name}\n\nPlease go to our website to access your bookings.\n\nKind regards,\nSkywalker Radiology'
    mail.send(msg)
    return True