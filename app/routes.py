from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename
from xlrd import XL_CELL_NUMBER, open_workbook

from . import db
from .models import AttendanceRecord, DutyAssignment, DutyPlan, Teacher

main_bp = Blueprint("main", __name__)


@main_bp.app_errorhandler(404)
def not_found(error):  # pragma: no cover - template driven
    return render_template("404.html"), 404


@main_bp.route("/")
def index():
    return redirect(url_for("main.today_plan"))


@main_bp.route("/plan/today", methods=["GET", "POST"])
def today_plan():
    today = date.today()
    return plan_for_day(today.strftime("%A"), today)


@main_bp.route("/plan/<day>", methods=["GET", "POST"])
def plan_for_day(day: str, target_date: date | None = None):
    day = day.capitalize()
    if target_date is None:
        date_param = request.args.get("date") or request.form.get("date")
        if date_param:
            try:
                target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "warning")
                target_date = date.today()
        else:
            target_date = date.today()

    all_plans = DutyPlan.query.order_by(DutyPlan.day_of_week).all()
    plan = DutyPlan.query.filter_by(day_of_week=day).first()
    if plan is None:
        flash(f"No dismissal plan found for {day}.", "warning")
        return render_template("plan.html", plan=None, day=day, target_date=target_date, all_plans=all_plans)

    if request.method == "POST":
        handle_attendance_submission(plan, target_date)
        return redirect(url_for("main.plan_for_day", day=day, date=target_date.isoformat()))

    attendance_map = load_attendance_map(plan, target_date)
    return render_template(
        "plan.html",
        plan=plan,
        attendance_map=attendance_map,
        day=day,
        target_date=target_date,
        all_plans=all_plans,
    )


@main_bp.route("/teachers")
def teachers():
    teacher_list = Teacher.query.order_by(Teacher.full_name).all()
    return render_template("teachers.html", teachers=teacher_list)


@main_bp.route("/import/teachers", methods=["GET", "POST"])
def import_teachers():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please choose an .xls file to upload.", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        if not filename.lower().endswith(".xls"):
            flash("Only .xls files are supported.", "danger")
            return redirect(request.url)

        upload_dir = Path(current_app.instance_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        file.save(file_path)

        try:
            imported_count = import_teachers_from_xls(file_path)
            flash(f"Successfully imported {imported_count} teachers.", "success")
        except Exception as exc:  # pragma: no cover - user feedback
            current_app.logger.exception("Failed to import teachers")
            flash(f"Failed to import teachers: {exc}", "danger")
        finally:
            if file_path.exists():
                file_path.unlink()

        return redirect(url_for("main.teachers"))

    return render_template("import_teachers.html")


def import_teachers_from_xls(path: Path) -> int:
    workbook = open_workbook(path, encoding_override="utf-8")
    sheet = workbook.sheet_by_index(0)

    headers = [str(sheet.cell_value(0, col)).strip().lower() for col in range(sheet.ncols)]
    expected_columns = {"num", "full name", "mobile", "email"}
    if not expected_columns.issubset(set(headers)):
        raise ValueError("The uploaded file does not contain the required columns: NUM, Full name, Mobile, Email")

    name_idx = headers.index("full name")
    mobile_idx = headers.index("mobile")
    email_idx = headers.index("email")

    count = 0
    for row_idx in range(1, sheet.nrows):
        full_name = to_string(sheet.cell(row_idx, name_idx))
        mobile = to_string(sheet.cell(row_idx, mobile_idx))
        email = to_string(sheet.cell(row_idx, email_idx)).lower()
        if not full_name or not email:
            continue

        teacher = Teacher.query.filter_by(email=email).first()
        if teacher:
            teacher.full_name = normalize_name(full_name)
            teacher.mobile = mobile
        else:
            teacher = Teacher(full_name=normalize_name(full_name), mobile=mobile, email=email)
            db.session.add(teacher)
        count += 1

    db.session.commit()
    return count


def normalize_name(name: str) -> str:
    return " ".join(part for part in name.split())


def to_string(cell) -> str:
    value = cell.value
    if cell.ctype == XL_CELL_NUMBER:
        if float(value).is_integer():
            return str(int(value))
        return str(value)
    return str(value).strip()


def handle_attendance_submission(plan: DutyPlan, target_date: date) -> None:
    for assignment in plan_assignments(plan):
        form_key = f"assignment-{assignment.id}"
        status = request.form.get(form_key)
        if status not in {"present", "absent", None}:
            continue
        record = AttendanceRecord.query.filter_by(assignment_id=assignment.id, date=target_date).first()
        previous_status = record.status if record else None

        if status is None:
            if record:
                db.session.delete(record)
                adjust_warnings(assignment, previous_status, None)
            continue

        if record is None:
            record = AttendanceRecord(assignment=assignment, date=target_date)
            db.session.add(record)
        record.status = status
        adjust_warnings(assignment, previous_status, status)

    db.session.commit()


def load_attendance_map(plan: DutyPlan, target_date: date) -> dict[int, AttendanceRecord | None]:
    records = (
        AttendanceRecord.query.join(DutyAssignment)
        .filter(DutyAssignment.section.has(plan_id=plan.id), AttendanceRecord.date == target_date)
        .all()
    )
    return {record.assignment_id: record for record in records}


def adjust_warnings(assignment: DutyAssignment, previous_status: str | None, new_status: str | None) -> None:
    teacher = assignment.teacher
    if not teacher:
        return

    if previous_status == "absent" and new_status != "absent" and teacher.warnings > 0:
        teacher.warnings -= 1
    if new_status == "absent" and previous_status != "absent":
        teacher.warnings += 1


def plan_assignments(plan: DutyPlan):
    for section in plan.sections:
        for assignment in section.assignments:
            yield assignment
