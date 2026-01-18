from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.base import MenuLink
from flask_admin.actions import action
from flask import flash
from markupsafe import Markup

from . import db
from .models import Teacher, DutyPlan, DutySection, DutyAssignment, AttendanceRecord, EmailNotificationLog


class TeacherView(ModelView):
    """Admin view for Teacher model with custom configurations."""
    column_list = ['id', 'full_name', 'email', 'mobile', 'warnings', 'late_count']
    column_searchable_list = ['full_name', 'email']
    column_filters = ['warnings', 'late_count']
    column_sortable_list = ['id', 'full_name', 'email', 'warnings', 'late_count']
    form_columns = ['full_name', 'email', 'mobile', 'warnings', 'late_count']
    
    column_labels = {
        'warnings': 'Absence Warnings',
        'late_count': 'Late Count'
    }
    
    @action('reset_warnings', 'Reset Absence Warnings', 'Are you sure you want to reset absence warnings for selected teachers?')
    def action_reset_warnings(self, ids):
        try:
            count = 0
            for teacher_id in ids:
                teacher = Teacher.query.get(teacher_id)
                if teacher:
                    teacher.warnings = 0
                    count += 1
            db.session.commit()
            flash(f'Successfully reset absence warnings for {count} teacher(s).', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error resetting warnings: {str(e)}', 'error')
    
    @action('reset_late_count', 'Reset Late Count', 'Are you sure you want to reset late count for selected teachers?')
    def action_reset_late_count(self, ids):
        try:
            count = 0
            for teacher_id in ids:
                teacher = Teacher.query.get(teacher_id)
                if teacher:
                    teacher.late_count = 0
                    count += 1
            db.session.commit()
            flash(f'Successfully reset late count for {count} teacher(s).', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error resetting late count: {str(e)}', 'error')
    
    @action('reset_all_counts', 'Reset Both Warnings & Late', 'Are you sure you want to reset both absence warnings and late count for selected teachers?')
    def action_reset_all_counts(self, ids):
        try:
            count = 0
            for teacher_id in ids:
                teacher = Teacher.query.get(teacher_id)
                if teacher:
                    teacher.warnings = 0
                    teacher.late_count = 0
                    count += 1
            db.session.commit()
            flash(f'Successfully reset all counts for {count} teacher(s).', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error resetting counts: {str(e)}', 'error')
    
    def __repr__(self):
        return 'Teachers'


class DutyPlanView(ModelView):
    """Admin view for DutyPlan model."""
    column_list = ['id', 'name', 'day_of_week', 'supervisor', 'team', 'is_daily_plan']
    column_searchable_list = ['name', 'supervisor', 'team']
    column_filters = ['day_of_week', 'is_daily_plan']
    form_columns = ['name', 'day_of_week', 'supervisor', 'team', 'is_daily_plan']


class DutySectionView(ModelView):
    """Admin view for DutySection model."""
    column_list = ['id', 'name', 'plan.name', 'order']
    column_searchable_list = ['name']
    column_filters = ['plan']
    form_columns = ['plan', 'name', 'order']


class DutyAssignmentView(ModelView):
    """Admin view for DutyAssignment model."""
    column_list = ['id', 'section.name', 'teacher.full_name', 'placeholder_name', 'place_task', 'order']
    column_searchable_list = ['placeholder_name', 'place_task']
    column_filters = ['section', 'teacher']
    form_columns = ['section', 'teacher', 'placeholder_name', 'place_task', 'order']


class AttendanceRecordView(ModelView):
    """Admin view for AttendanceRecord model."""
    column_list = ['id', 'assignment.teacher.full_name', 'assignment.section.name', 'date', 'status', 'notes']
    column_searchable_list = ['notes']
    column_filters = ['date', 'status', 'assignment']
    column_sortable_list = ['id', 'date', 'status']
    form_columns = ['assignment', 'date', 'status', 'notes']
    
    @action('delete_selected', 'Delete Selected', 'Are you sure you want to delete selected attendance records?')
    def action_delete_selected(self, ids):
        try:
            count = 0
            for record_id in ids:
                record = AttendanceRecord.query.get(record_id)
                if record:
                    db.session.delete(record)
                    count += 1
            db.session.commit()
            flash(f'Successfully deleted {count} attendance record(s).', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting records: {str(e)}', 'error')
    
    @action('clear_today', 'Clear Today\'s Records', 'Are you sure you want to clear all of today\'s attendance records?')
    def action_clear_today(self, ids):
        try:
            from datetime import date
            today = date.today()
            count = AttendanceRecord.query.filter_by(date=today).delete()
            db.session.commit()
            flash(f'Successfully cleared {count} attendance record(s) for today.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error clearing records: {str(e)}', 'error')


class EmailNotificationLogView(ModelView):
    """Admin view for EmailNotificationLog model."""
    column_list = ['id', 'teacher_email', 'date', 'status', 'sent_at']
    column_searchable_list = ['teacher_email']
    column_filters = ['date', 'status', 'sent_at']
    column_sortable_list = ['id', 'date', 'sent_at']
    form_columns = ['teacher_email', 'date', 'status']


def init_admin(app):
    """Initialize Flask-Admin with the Flask app."""
    admin = Admin(app, name='Dismissal Checker Admin')
    
    # Add model views
    admin.add_view(TeacherView(Teacher, db.session, name='Teachers'))
    admin.add_view(DutyPlanView(DutyPlan, db.session, name='Duty Plans'))
    admin.add_view(DutySectionView(DutySection, db.session, name='Duty Sections'))
    admin.add_view(DutyAssignmentView(DutyAssignment, db.session, name='Duty Assignments'))
    admin.add_view(AttendanceRecordView(AttendanceRecord, db.session, name='Attendance Records'))
    admin.add_view(EmailNotificationLogView(EmailNotificationLog, db.session, name='Email Logs'))
    
    # Add a link back to the main application
    admin.add_link(MenuLink(name='Back to App', url='/'))
    
    return admin