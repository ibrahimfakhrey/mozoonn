from __future__ import annotations

from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db


class Teacher(db.Model):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    mobile: Mapped[str | None] = mapped_column(db.String(32))
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    warnings: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    assignments: Mapped[list["DutyAssignment"]] = relationship(back_populates="teacher")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Teacher {self.full_name} ({self.email})>"


class DutyPlan(db.Model):
    __tablename__ = "duty_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    day_of_week: Mapped[str] = mapped_column(db.String(16), nullable=False, unique=True)
    supervisor: Mapped[str] = mapped_column(db.String(120), nullable=False)
    team: Mapped[str] = mapped_column(db.String(255), nullable=True)

    sections: Mapped[list["DutySection"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="DutySection.order"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DutyPlan {self.day_of_week}>"


class DutySection(db.Model):
    __tablename__ = "duty_sections"
    __table_args__ = (UniqueConstraint("plan_id", "name", name="uix_plan_section"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("duty_plans.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)

    plan: Mapped[DutyPlan] = relationship(back_populates="sections")
    assignments: Mapped[list["DutyAssignment"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", order_by="DutyAssignment.order"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DutySection {self.name} ({self.plan.day_of_week})>"


class DutyAssignment(db.Model):
    __tablename__ = "duty_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("duty_sections.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"), nullable=True)
    placeholder_name: Mapped[str] = mapped_column(db.String(120), nullable=True)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    place_task: Mapped[str | None] = mapped_column(db.String(255))

    section: Mapped[DutySection] = relationship(back_populates="assignments")
    teacher: Mapped[Teacher | None] = relationship(back_populates="assignments")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="assignment", cascade="all, delete-orphan")

    @property
    def display_name(self) -> str:
        return self.teacher.full_name if self.teacher else (self.placeholder_name or "Unassigned")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DutyAssignment {self.display_name} ({self.section.plan.day_of_week})>"


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("assignment_id", "date", name="uix_assignment_date"),
        CheckConstraint("status in ('present', 'absent')", name="ck_status_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("duty_assignments.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(db.String(16), nullable=False)

    assignment: Mapped[DutyAssignment] = relationship(back_populates="attendance_records")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AttendanceRecord {self.assignment_id} {self.date} {self.status}>"
