from __future__ import annotations

from datetime import date
from pathlib import Path

import click

from . import db
from .models import AttendanceRecord, DutyAssignment, DutyPlan, DutySection
from .plan_loader import load_plan


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PLAN_FILE = DATA_DIR / "dismissal_plan.json"


def register(app):
    @app.cli.command("load-plan")
    @click.option("--plan-file", type=click.Path(exists=True, dir_okay=False), default=str(PLAN_FILE))
    def load_plan_command(plan_file: str) -> None:
        """Load the dismissal plan from a JSON file into the database."""
        plan_path = Path(plan_file)
        if not plan_path.exists():
            click.echo(f"Plan file {plan_path} does not exist.")
            return
        load_plan(plan_path)
        click.echo("Dismissal plan loaded.")

    @app.cli.command("clear-attendance")
    @click.option("--day", type=str, help="Limit clearing to a specific day of the week (e.g. Sunday).")
    def clear_attendance(day: str | None) -> None:
        """Clear attendance records, optionally filtered by day of week."""
        query = AttendanceRecord.query
        if day:
            day = day.capitalize()
            query = query.join(DutyAssignment).join(DutySection).join(DutyPlan).filter(DutyPlan.day_of_week == day)
        count = query.delete(synchronize_session=False)
        db.session.commit()
        click.echo(f"Removed {count} attendance records.")

    @app.cli.command("today-plan")
    def today_plan() -> None:
        """Print the assignments scheduled for today."""
        current_day = date.today().strftime("%A")
        plan = DutyPlan.query.filter_by(day_of_week=current_day).first()
        if not plan:
            click.echo(f"No plan found for {current_day}.")
            return
        click.echo(f"Supervisor: {plan.supervisor}")
        click.echo(f"Team: {plan.team}")
        for section in plan.sections:
            click.echo(f"\n{section.name}")
            for assignment in section.assignments:
                teacher_name = assignment.teacher.full_name if assignment.teacher else assignment.placeholder_name
                click.echo(f"  {assignment.order}. {teacher_name} - {assignment.place_task or 'No task specified'}")
