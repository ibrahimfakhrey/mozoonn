import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import logging
from flask import render_template
from app.models import EmailNotificationLog
from app import db

# Email configuration - Using Gmail (PythonAnywhere whitelisted)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "amsprog2022@gmail.com"
EMAIL_PASSWORD = "xfleslznraphvqgc"

# Admin emails to CC on all notifications
ADMIN_CC_EMAILS = [
    "hadeer.twfik@ams-benha.com",
    "yasser.alaraby@ams-benha.com",
    "islam.qamar@ams-benha.com",
    "mohamad.mosalam@ams-benha.com",
    "ibrahim.fakhry@ams-benha.com"
]

def send_attendance_notification(teacher_email, teacher_name, status, day, attendance_date, section=None, task_place=None, supervisor=None, warnings=None, notes=None):
    """
    Send an HTML email notification to a teacher about their attendance status (absent or late).
    Prevents duplicate emails for the same teacher on the same day.
    
    Args:
        teacher_email (str): Teacher's email address
        teacher_name (str): Teacher's full name
        status (str): 'absent' or 'late'
        day (str): Day of the week
        attendance_date (date): Date of the attendance
        section (str): Section name if applicable
        task_place (str): Task or place assignment
        supervisor (str): Supervisor name if applicable
    
    Returns:
        dict: Result with success status and message
    """
    try:
        # Check if email was already sent for this teacher on this date
        # Skip duplicate check for Ibrahim (testing purposes)
        is_ibrahim_test = "ibrahim" in teacher_email.lower() or "ibrahim" in teacher_name.lower()
        
        if not is_ibrahim_test:
            existing_log = EmailNotificationLog.query.filter_by(
                teacher_email=teacher_email,
                date=attendance_date
            ).first()
            
            if existing_log:
                logging.info(f"Email already sent to {teacher_email} on {attendance_date}. Skipping duplicate.")
                return {
                    'success': True,
                    'message': f'Email already sent to {teacher_name} today. Skipping duplicate.',
                    'skipped': True
                }
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = teacher_email
        msg['Cc'] = ', '.join(ADMIN_CC_EMAILS)
        msg['Subject'] = f"Attendance Notification - {status.title()} - {day}, {attendance_date}"
        
        # Render HTML email template
        html_body = render_template('email_template.html',
                                  teacher_name=teacher_name,
                                  status=status,
                                  date=attendance_date.strftime('%Y-%m-%d'),
                                  day=day,
                                  section=section or 'N/A',
                                  task_place=task_place or 'N/A',
                                  supervisor=supervisor,
                                  warnings=warnings,
                                  notes=notes)
        
        # Create HTML part
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        all_recipients = [teacher_email] + ADMIN_CC_EMAILS
        logging.info(f"Attempting to send {status} notification email to {teacher_email} (CC: {ADMIN_CC_EMAILS})")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            logging.info(f"Logging in to Gmail SMTP server...")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            logging.info(f"Login successful, sending email...")
            server.sendmail(EMAIL_ADDRESS, all_recipients, msg.as_string())
            logging.info(f"Email sent successfully to {teacher_email} and CC'd admins")
        
        # Log the email notification to prevent duplicates
        email_log = EmailNotificationLog(
            teacher_email=teacher_email,
            date=attendance_date,
            status=status
        )
        db.session.add(email_log)
        db.session.commit()
        
        return {
            'success': True,
            'message': f'{status.title()} notification sent successfully to {teacher_name}',
            'skipped': False
        }
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Gmail authentication failed: {str(e)}. Please check if 2-Factor Authentication is enabled and app password is correct."
        logging.error(error_msg)
        return {'success': False, 'message': error_msg}
    except Exception as e:
        error_msg = f"Failed to send {status} notification to {teacher_name}: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'message': error_msg}


def send_bulk_attendance_notifications(attendance_data):
    """
    Send attendance notifications to multiple teachers.
    
    Args:
        attendance_data (list): List of dictionaries containing teacher attendance data
    
    Returns:
        dict: Summary of email sending results
    """
    results = {
        'sent': 0,
        'skipped': 0,
        'failed': 0,
        'messages': []
    }
    
    for data in attendance_data:
        if data['status'] in ['absent', 'late']:
            result = send_attendance_notification(
                teacher_email=data['email'],
                teacher_name=data['name'],
                status=data['status'],
                day=data['day'],
                attendance_date=data['date'],
                section=data.get('section'),
                task_place=data.get('task_place'),
                supervisor=data.get('supervisor'),
                warnings=data.get('warnings'),
                notes=data.get('notes')
            )
            
            if result['success']:
                if result.get('skipped'):
                    results['skipped'] += 1
                else:
                    results['sent'] += 1
            else:
                results['failed'] += 1
            
            results['messages'].append(result['message'])
    
    return results


def test_email_connection():
    """
    Test the email connection to Gmail SMTP server.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        logging.info("Testing email connection...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            logging.info("Email connection test successful")
            return True
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"Gmail authentication failed: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Email connection test failed: {str(e)}")
        return False


def send_absence_warning_email(teacher_email, teacher_name, warning_number, attendance_date, day, section=None, task_place=None):
    """
    Send an absence warning email (for 1st or 2nd warning).
    
    Args:
        teacher_email: Teacher's email address
        teacher_name: Teacher's full name
        warning_number: Current warning count (1 or 2)
        attendance_date: Date of the absence
        day: Day of the week
        section: Section name
        task_place: Task or place assignment
    
    Returns:
        dict: Result with success status and message
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = teacher_email
        msg['Cc'] = ', '.join(ADMIN_CC_EMAILS)
        msg['Subject'] = f"⚠️ Absence Warning {warning_number}/3 - {day}, {attendance_date}"

        html_body = render_template('email_absence_warning.html',
                                  teacher_name=teacher_name,
                                  warning_number=warning_number,
                                  date=attendance_date.strftime('%Y-%m-%d'),
                                  day=day,
                                  section=section or 'N/A',
                                  task_place=task_place or 'N/A')
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        all_recipients = [teacher_email] + ADMIN_CC_EMAILS
        logging.info(f"Sending absence warning {warning_number} email to {teacher_email} (CC: admins)")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, all_recipients, msg.as_string())
            logging.info(f"Absence warning email sent successfully to {teacher_email} and CC'd admins")

        return {'success': True, 'message': f'Absence warning {warning_number} sent to {teacher_name}'}
        
    except Exception as e:
        error_msg = f"Failed to send absence warning to {teacher_name}: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'message': error_msg}


def send_absence_deduction_email(teacher_email, teacher_name, attendance_date, day, section=None, task_place=None, deduction_type="half_day", warning_number=2):
    """
    Send a salary deduction email for absence.

    Args:
        teacher_email: Teacher's email address
        teacher_name: Teacher's full name
        attendance_date: Date of the absence
        day: Day of the week
        section: Section name
        task_place: Task or place assignment
        deduction_type: 'half_day' (1/2 day for 2nd absence) or 'full_day' (1 day for 3rd absence)
        warning_number: The warning number (2 or 3)

    Returns:
        dict: Result with success status and message
    """
    try:
        if deduction_type == "half_day":
            template = 'email_absence_half_day_deduction.html'
            subject = f"🚨 SALARY DEDUCTION NOTICE - 1/2 Day - {day}, {attendance_date}"
            deduction_text = "1/2 day"
        else:  # full_day
            template = 'email_absence_full_day_deduction.html'
            subject = f"🚨 SALARY DEDUCTION NOTICE - 1 Day - {day}, {attendance_date}"
            deduction_text = "1 day"

        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = teacher_email
        msg['Cc'] = ', '.join(ADMIN_CC_EMAILS)
        msg['Subject'] = subject

        html_body = render_template(template,
                                  teacher_name=teacher_name,
                                  date=attendance_date.strftime('%Y-%m-%d'),
                                  day=day,
                                  section=section or 'N/A',
                                  task_place=task_place or 'N/A',
                                  warning_number=warning_number)

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        all_recipients = [teacher_email] + ADMIN_CC_EMAILS
        logging.info(f"Sending {deduction_text} absence deduction email to {teacher_email} (CC: admins)")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, all_recipients, msg.as_string())
            logging.info(f"{deduction_text} deduction email sent successfully to {teacher_email} and CC'd admins")

        return {'success': True, 'message': f'{deduction_text} deduction notice sent to {teacher_name}'}
        
    except Exception as e:
        error_msg = f"Failed to send deduction notice to {teacher_name}: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'message': error_msg}


def send_late_warning_email(teacher_email, teacher_name, late_number, attendance_date, day, section=None, task_place=None):
    """
    Send a late warning email (for 1st late only now).

    Args:
        teacher_email: Teacher's email address
        teacher_name: Teacher's full name
        late_number: Current late count (1)
        attendance_date: Date of the late arrival
        day: Day of the week
        section: Section name
        task_place: Task or place assignment

    Returns:
        dict: Result with success status and message
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = teacher_email
        msg['Cc'] = ', '.join(ADMIN_CC_EMAILS)
        msg['Subject'] = f"⏰ Late Warning {late_number}/3 - {day}, {attendance_date}"

        html_body = render_template('email_late_warning.html',
                                  teacher_name=teacher_name,
                                  late_number=late_number,
                                  date=attendance_date.strftime('%Y-%m-%d'),
                                  day=day,
                                  section=section or 'N/A',
                                  task_place=task_place or 'N/A')

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        all_recipients = [teacher_email] + ADMIN_CC_EMAILS
        logging.info(f"Sending late warning {late_number} email to {teacher_email} (CC: admins)")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, all_recipients, msg.as_string())
            logging.info(f"Late warning email sent successfully to {teacher_email} and CC'd admins")

        return {'success': True, 'message': f'Late warning {late_number} sent to {teacher_name}'}
        
    except Exception as e:
        error_msg = f"Failed to send late warning to {teacher_name}: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'message': error_msg}


def send_late_deduction_email(teacher_email, teacher_name, attendance_date, day, section=None, task_place=None, deduction_type="quarter_day", late_number=2):
    """
    Send a salary deduction email for late arrival.

    Args:
        teacher_email: Teacher's email address
        teacher_name: Teacher's full name
        attendance_date: Date of the late arrival
        day: Day of the week
        section: Section name
        task_place: Task or place assignment
        deduction_type: 'quarter_day' (1/4 day for 2nd late) or 'half_day' (1/2 day for 3rd late)
        late_number: The late count (2 or 3)

    Returns:
        dict: Result with success status and message
    """
    try:
        if deduction_type == "quarter_day":
            template = 'email_late_quarter_day_deduction.html'
            subject = f"🚨 SALARY DEDUCTION NOTICE - 1/4 Day - {day}, {attendance_date}"
            deduction_text = "1/4 day"
        else:  # half_day
            template = 'email_late_half_day_deduction.html'
            subject = f"🚨 SALARY DEDUCTION NOTICE - 1/2 Day - {day}, {attendance_date}"
            deduction_text = "1/2 day"

        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = teacher_email
        msg['Cc'] = ', '.join(ADMIN_CC_EMAILS)
        msg['Subject'] = subject

        html_body = render_template(template,
                                  teacher_name=teacher_name,
                                  date=attendance_date.strftime('%Y-%m-%d'),
                                  day=day,
                                  section=section or 'N/A',
                                  task_place=task_place or 'N/A',
                                  late_number=late_number)

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        all_recipients = [teacher_email] + ADMIN_CC_EMAILS
        logging.info(f"Sending {deduction_text} late deduction email to {teacher_email} (CC: admins)")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, all_recipients, msg.as_string())
            logging.info(f"{deduction_text} late deduction email sent successfully to {teacher_email} and CC'd admins")

        return {'success': True, 'message': f'{deduction_text} deduction notice sent to {teacher_name}'}
        
    except Exception as e:
        error_msg = f"Failed to send deduction notice to {teacher_name}: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'message': error_msg}