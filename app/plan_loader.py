from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from . import db
from .models import DutyAssignment, DutyPlan, DutySection, Teacher


DAY_ORDER = {"Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}


def load_plan(path: Path) -> None:
    """Load a dismissal plan from a JSON file into the database."""
    payload = json.loads(path.read_text(encoding="utf-8"))

    existing_plans = {plan.day_of_week: plan for plan in db.session.scalars(select(DutyPlan)).all()}

    for plan_data in payload:
        day = plan_data["day"]
        plan = existing_plans.get(day)
        if plan is None:
            plan = DutyPlan(day_of_week=day)
            db.session.add(plan)
            existing_plans[day] = plan
        plan.supervisor = plan_data.get("supervisor", "")
        plan.team = plan_data.get("team")

        # Clear existing sections/assignments to reload fresh data
        plan.sections.clear()
        for section_order, section in enumerate(plan_data.get("sections", []), start=1):
            section_model = DutySection(name=section["name"], order=section_order)
            plan.sections.append(section_model)
            for assignment_data in section.get("assignments", []):
                assignment = DutyAssignment(
                    order=assignment_data.get("order", 0),
                    place_task=assignment_data.get("place_task"),
                )
                teacher_name = assignment_data.get("teacher")
                if teacher_name:
                    teacher = resolve_teacher_by_name(teacher_name)
                    if teacher:
                        assignment.teacher = teacher
                    else:
                        assignment.placeholder_name = teacher_name
                else:
                    assignment.placeholder_name = assignment_data.get("placeholder_name")
                section_model.assignments.append(assignment)

    db.session.commit()


def resolve_teacher_by_name(name: str) -> Teacher | None:
    """Attempt to match a teacher by their full name ignoring double spaces and case."""
    normalized = " ".join(part for part in name.split())
    stmt = select(Teacher).where(db.func.lower(Teacher.full_name) == normalized.lower())
    return db.session.scalar(stmt)


def export_plan() -> list[dict[str, Any]]:
    """Serialize the current plan state to a JSON-compatible structure."""
    plans = []
    for plan in DutyPlan.query.order_by(db.case(DAY_ORDER, value=DutyPlan.day_of_week)).all():
        sections = []
        for section in plan.sections:
            assignments = []
            for assignment in section.assignments:
                assignments.append(
                    {
                        "order": assignment.order,
                        "teacher": assignment.teacher.full_name if assignment.teacher else assignment.placeholder_name,
                        "place_task": assignment.place_task,
                    }
                )
            sections.append({"name": section.name, "assignments": assignments})
        plans.append({"day": plan.day_of_week, "supervisor": plan.supervisor, "team": plan.team, "sections": sections})
    return plans
