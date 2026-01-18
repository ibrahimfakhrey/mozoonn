#!/usr/bin/env python3
"""
Script to send test emails to all admins demonstrating the new warning/deduction system.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

# Email configuration
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "support@ams-benha.com"
EMAIL_PASSWORD = "Zo2lot[1991]"

# Admin emails to send test emails to
ADMIN_EMAILS = [
    "hadeer.twfik@ams-benha.com",
    "yasser.alaraby@ams-benha.com",
    "islam.qamar@ams-benha.com",
    "mohamad.mosalam@ams-benha.com",
    "ibrahim.fakhry@ams-benha.com"
]

today = date.today()
today_str = today.strftime('%Y-%m-%d')
day_name = today.strftime('%A')

def create_test_email_html():
    """Create a comprehensive test email showing all notification types."""

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test - New Notification System</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
            color: #333333;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .test-banner {{
            background-color: #17a2b8;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            border-radius: 8px;
        }}
        .section h2 {{
            margin-top: 0;
            padding-bottom: 10px;
            border-bottom: 2px solid;
        }}
        .late-section {{
            background-color: #fff3cd;
            border: 2px solid #ffc107;
        }}
        .late-section h2 {{
            color: #856404;
            border-color: #ffc107;
        }}
        .absent-section {{
            background-color: #f8d7da;
            border: 2px solid #dc3545;
        }}
        .absent-section h2 {{
            color: #721c24;
            border-color: #dc3545;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .warning {{
            background-color: #ffc107;
            color: #212529;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .deduction {{
            background-color: #dc3545;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .deduction-orange {{
            background-color: #fd7e14;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .footer {{
            background-color: #343a40;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .note {{
            background-color: #d4edda;
            border: 2px solid #28a745;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="test-banner">
            THIS IS A TEST - New Notification System
        </div>

        <div class="content">
            <div class="note">
                <strong>Dear Team,</strong><br><br>
                This is a <strong>TEST EMAIL</strong> to demonstrate the new dismissal duty warning and deduction notification system.
                Below you will see examples of all the different types of emails that teachers will receive based on their attendance status.
                <br><br>
                <strong>Date:</strong> {today_str}<br>
                <strong>Day:</strong> {day_name}
            </div>

            <div class="section late-section">
                <h2>LATE ARRIVAL NOTIFICATIONS</h2>
                <p>Teachers who arrive late to their dismissal duty will receive the following notifications:</p>

                <table>
                    <tr>
                        <th>Late Count</th>
                        <th>Action</th>
                        <th>Email Type</th>
                    </tr>
                    <tr>
                        <td><strong>1st Late</strong></td>
                        <td><span class="warning">WARNING</span></td>
                        <td>Late Warning Email (1/3)</td>
                    </tr>
                    <tr>
                        <td><strong>2nd Late</strong></td>
                        <td><span class="deduction-orange">1/4 DAY DEDUCTION</span></td>
                        <td>Quarter Day Salary Deduction Notice</td>
                    </tr>
                    <tr>
                        <td><strong>3rd Late</strong></td>
                        <td><span class="deduction">1/2 DAY DEDUCTION</span></td>
                        <td>Half Day Salary Deduction Notice<br><em>(Counter resets to 0)</em></td>
                    </tr>
                </table>
            </div>

            <div class="section absent-section">
                <h2>ABSENCE NOTIFICATIONS</h2>
                <p>Teachers who are absent from their dismissal duty will receive the following notifications:</p>

                <table>
                    <tr>
                        <th>Absence Count</th>
                        <th>Action</th>
                        <th>Email Type</th>
                    </tr>
                    <tr>
                        <td><strong>1st Absence</strong></td>
                        <td><span class="warning">WARNING</span></td>
                        <td>Absence Warning Email (1/3)</td>
                    </tr>
                    <tr>
                        <td><strong>2nd Absence</strong></td>
                        <td><span class="deduction">1/2 DAY DEDUCTION</span></td>
                        <td>Half Day Salary Deduction Notice</td>
                    </tr>
                    <tr>
                        <td><strong>3rd Absence</strong></td>
                        <td><span class="deduction">1 FULL DAY DEDUCTION</span></td>
                        <td>Full Day Salary Deduction Notice<br><em>(Counter resets to 0)</em></td>
                    </tr>
                </table>
            </div>

            <div class="note">
                <strong>Important Notes:</strong>
                <ul>
                    <li>All notification emails will be sent to the teacher AND CC'd to all administrators</li>
                    <li>After the maximum deduction (3rd late or 3rd absence), the counter resets to 0</li>
                    <li>The system prevents duplicate emails to the same teacher on the same day</li>
                    <li>Emails are sent from: <strong>support@ams-benha.com</strong></li>
                </ul>
            </div>
        </div>

        <div class="footer">
            <h3>AMS School - Dismissal Duty Management System</h3>
            <p>This is a test email - No action required</p>
        </div>
    </div>
</body>
</html>
"""
    return html


def send_test_emails():
    """Send test emails to all admin recipients."""

    print("=" * 60)
    print("Sending Test Emails - New Notification System")
    print("=" * 60)

    html_content = create_test_email_html()

    try:
        print(f"\nConnecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print(f"Logging in as: {EMAIL_ADDRESS}")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("Login successful!\n")

            for admin_email in ADMIN_EMAILS:
                try:
                    msg = MIMEMultipart('alternative')
                    msg['From'] = EMAIL_ADDRESS
                    msg['To'] = admin_email
                    msg['Subject'] = f"TEST - New Dismissal Duty Notification System - {today_str}"

                    html_part = MIMEText(html_content, 'html')
                    msg.attach(html_part)

                    server.sendmail(EMAIL_ADDRESS, admin_email, msg.as_string())
                    print(f"[OK] Sent to: {admin_email}")

                except Exception as e:
                    print(f"[FAILED] {admin_email}: {str(e)}")

            print("\n" + "=" * 60)
            print("Test emails sent successfully!")
            print("=" * 60)

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n[ERROR] Authentication failed: {str(e)}")
        print("Please check the email address and password.")
    except Exception as e:
        print(f"\n[ERROR] Failed to send emails: {str(e)}")


if __name__ == "__main__":
    send_test_emails()
