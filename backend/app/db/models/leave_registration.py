"""LeaveRegistration model — one employee leave on the leave register.

The leave-tracker scheduled task reads the **concrete deadline date**
columns (``medical_period_end`` etc.) computed at log-leave time and does
pure date arithmetic — it never calls the LLM. ``entitlement`` keeps the
retrieved law text for display / audit.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LeaveRegistration(Base, TimestampMixin):
    """An employee leave entry on the leave register."""

    __tablename__ = "leave_registrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Employee
    employee_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False)

    # Leave
    leave_type: Mapped[str] = mapped_column(
        String(40), nullable=False
    )  # annual/maternity/sick/work_injury/marriage/parental/paternity
    leave_start: Mapped[date] = mapped_column(Date, nullable=False)
    expected_return: Mapped[date | None] = mapped_column(Date, nullable=True)
    intermittent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Tenure (for entitlement computation)
    accumulated_work_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_work_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    normal_schedule: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Approval
    leave_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    leave_approval_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    medical_certificate_received: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Entitlement (retrieved law text — NOT hardcoded)
    entitlement: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_used: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Concrete deadline dates — computed at log-leave time; cron does pure
    # date arithmetic over these (no LLM at scheduled-run time).
    medical_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    maternity_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    work_injury_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    annual_carryover_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Social insurance / capacity
    social_insurance_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    labor_capacity_assessment: Mapped[str | None] = mapped_column(String(40), nullable=True)
    return_to_work_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Annual leave carryover
    annual_leave_carryover: Mapped[str | None] = mapped_column(String(40), nullable=True)
    unpaid_leave_compensation: Mapped[str | None] = mapped_column(String(40), nullable=True)

    controlling_sources: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active / completed / cancelled
    last_updated: Mapped[date | None] = mapped_column(Date, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<LeaveRegistration(id={self.id}, employee={self.employee_name}, "
            f"type={self.leave_type}, status={self.status})>"
        )
