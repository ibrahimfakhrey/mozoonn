#!/usr/bin/env python3
"""
Automated scheduler for sending daily reports and individual notifications.
This script runs at 4:00 PM Cairo time to:
1. Send daily absent teachers report to specified emails
2. Send individual notifications to absent teachers with their warnings
"""

import schedule
import time
import logging
from datetime import date, datetime
import pytz
from app import create_app, db
from app.models import AttendanceRecord, DutyAssignment, DutyPlan, DutySection, Teacher
from app.email_service import send_attendance_notification
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

def send_daily_report():
    """Send daily absent teachers report to specified emails"""
    try:
        app = create_app()
        with app.app_context():
            today = date.today()
            today_day_name = today.strftime("%A")
            
            logging.info(f"Starting daily report generation for {today}")
            
            # Get today's plan
            plan = DutyPlan.query.filter_by(day_of_week=today_day_name).first()
            
            if not plan:
                logging.warning(f'No plan found for {today_day_name}')
                return
            
            # Get absent teachers for today
            absent_records = db.session.query(
                AttendanceRecord, Teacher, DutyAssignment, DutySection
            ).join(
                DutyAssignment, AttendanceRecord.assignment_id == DutyAssignment.id
            ).join(
                Teacher, DutyAssignment.teacher_id == Teacher.id
            ).join(
                DutySection, DutyAssignment.section_id == DutySection.id
            ).filter(
                AttendanceRecord.date == today,
                AttendanceRecord.status == 'absent'
            ).all()
            
            absent_teachers = []
            for record, teacher, assignment, section in absent_records:
                absent_teachers.append({
                    'name': teacher.full_name,
                    'email': teacher.email,
                    'section': section.name,
                    'task_place': assignment.place_task,
                    'supervisor': plan.supervisor,
                    'warnings': teacher.warnings,
                    'notes': record.notes
                })
            
            # Send email report
            if absent_teachers:
                try:
                    # Create email content
                    email_content = f"""
                    <h2>Daily Absent Teachers Report - {today.strftime('%Y-%m-%d')}</h2>
                    <p>Total absent teachers: {len(absent_teachers)}</p>
                    <table border="1" style="border-collapse: collapse; width: 100%;">
                        <tr style="background-color: #f2f2f2;">
                            <th style="padding: 8px;">Teacher Name</th>
                            <th style="padding: 8px;">Section</th>
                            <th style="padding: 8px;">Task/Place</th>
                            <th style="padding: 8px;">Supervisor</th>
                            <th style="padding: 8px;">Warnings</th>
                        </tr>
                    """
                    
                    for teacher in absent_teachers:
                        email_content += f"""
                        <tr>
                            <td style="padding: 8px;">{teacher['name']}</td>
                            <td style="padding: 8px;">{teacher['section']}</td>
                            <td style="padding: 8px;">{teacher['task_place'] or 'N/A'}</td>
                            <td style="padding: 8px;">{teacher['supervisor'] or 'N/A'}</td>
                            <td style="padding: 8px;">{teacher['warnings'] or 0}</td>
                        </tr>
                        """
                    
                    email_content += "</table>"
                    
                    # Send email using SMTP
                    recipients = ["islam.qamar@ams-benha.com", "ibrahimfakhreyams@gmail.com"]
                    
                    msg = MIMEMultipart('alternative')
                    msg['From'] = "amsprog2022@gmail.com"
                    msg['To'] = ", ".join(recipients)
                    msg['Subject'] = f"Daily Absent Teachers Report - {today.strftime('%Y-%m-%d')}"
                    
                    html_part = MIMEText(email_content, 'html')
                    msg.attach(html_part)
                    
                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                        server.starttls()
                        server.login("amsprog2022@gmail.com", "xfleslznraphvqgc")
                        server.send_message(msg)
                    
                    logging.info(f'Daily report sent successfully to {", ".join(recipients)} with {len(absent_teachers)} absent teachers')
                    
                except Exception as email_error:
                    logging.error(f'Failed to send daily report: {str(email_error)}')
            else:
                logging.info('No absent teachers today - no daily report sent')
                
    except Exception as e:
        logging.error(f'Error in daily report generation: {str(e)}')

def send_individual_notifications():
    """Send individual notifications to absent teachers with their warnings"""
    try:
        app = create_app()
        with app.app_context():
            today = date.today()
            day_name = today.strftime("%A")
            
            logging.info(f"Starting individual notifications for {today}")
            
            # Get today's duty plan
            plan = DutyPlan.query.filter_by(day_of_week=day_name).first()
            
            if not plan:
                logging.warning(f'No duty plan found for {day_name}')
                return
            
            # Query for absent teachers today
            absent_records = db.session.query(
                AttendanceRecord, Teacher, DutyAssignment, DutySection
            ).join(
                DutyAssignment, AttendanceRecord.assignment_id == DutyAssignment.id
            ).join(
                Teacher, DutyAssignment.teacher_id == Teacher.id
            ).join(
                DutySection, DutyAssignment.section_id == DutySection.id
            ).filter(
                AttendanceRecord.date == today,
                AttendanceRecord.status == 'absent',
                DutySection.plan_id == plan.id
            ).all()
            
            if not absent_records:
                logging.info('No absent teachers found for individual notifications')
                return
            
            # Send individual notifications to each absent teacher
            sent_count = 0
            skipped_count = 0
            failed_count = 0
            
            for record, teacher, assignment, section in absent_records:
                try:
                    result = send_attendance_notification(
                        teacher_email=teacher.email,
                        teacher_name=teacher.full_name,
                        status='absent',
                        day=day_name,
                        attendance_date=today,
                        section=section.name,
                        task_place=assignment.place_task,
                        supervisor=plan.supervisor,
                        warnings=teacher.warnings,
                        notes=record.notes
                    )
                    
                    if result['success']:
                        if result.get('skipped', False):
                            skipped_count += 1
                        else:
                            sent_count += 1
                    else:
                        failed_count += 1
                        logging.error(f'Failed to send email to {teacher.full_name}: {result["message"]}')
                        
                except Exception as e:
                    failed_count += 1
                    logging.error(f'Error sending email to {teacher.full_name}: {str(e)}')
            
            # Log summary
            total_teachers = len(absent_records)
            logging.info(f'Individual notifications summary for {total_teachers} absent teachers: {sent_count} sent, {skipped_count} skipped, {failed_count} failed')
            
    except Exception as e:
        logging.error(f'Error in individual notifications: {str(e)}')

def run_daily_tasks():
    """Run both daily report and individual notifications"""
    logging.info("=== Starting scheduled daily tasks ===")
    send_daily_report()
    send_individual_notifications()
    logging.info("=== Completed scheduled daily tasks ===")

def main():
    """Main scheduler function"""
    # Set Cairo timezone
    cairo_tz = pytz.timezone('Africa/Cairo')
    
    # Schedule the task to run at 4:00 PM Cairo time
    schedule.every().day.at("16:00").do(run_daily_tasks)
    
    logging.info("Scheduler started. Waiting for 4:00 PM Cairo time...")
    logging.info("Next run scheduled for: 4:00 PM Cairo time")
    
    while True:
        # Check if it's time to run
        schedule.run_pending()
        
        # Sleep for 1 minute before checking again
        time.sleep(60)

if __name__ == "__main__":
    main()