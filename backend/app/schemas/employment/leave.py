"""LeaveRegistration request / response schemas."""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

LeaveType = Literal[
    "annual", "maternity", "sick", "work_injury", "marriage", "parental", "paternity"
]
LeaveStatus = Literal["active", "completed", "cancelled"]


class LeaveRegistrationCreate(BaseSchema):
    employee_id: str | None = Field(default=None, max_length=100)
    employee_name: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    jurisdiction: str = Field(max_length=100)
    leave_type: LeaveType
    leave_start: date
    expected_return: date | None = None
    intermittent: bool = False
    accumulated_work_years: int | None = None
    company_work_years: int | None = None
    normal_schedule: str | None = Field(default=None, max_length=100)
    leave_approved: bool = False
    leave_approval_date: date | None = None
    medical_certificate_received: bool = False
    entitlement: str | None = None
    time_used: str | None = None
    # Concrete deadline dates may be supplied (computed at log-leave time).
    medical_period_end: date | None = None
    maternity_return_date: date | None = None
    work_injury_period_end: date | None = None
    annual_carryover_deadline: date | None = None
    social_insurance_status: str | None = Field(default=None, max_length=100)
    labor_capacity_assessment: str | None = Field(default=None, max_length=40)
    return_to_work_confirmed: bool = False
    annual_leave_carryover: str | None = Field(default=None, max_length=40)
    unpaid_leave_compensation: str | None = Field(default=None, max_length=40)
    controlling_sources: str | None = None
    notes: str | None = None


class LeaveRegistrationUpdate(BaseSchema):
    employee_name: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    jurisdiction: str | None = Field(default=None, max_length=100)
    expected_return: date | None = None
    leave_approved: bool | None = None
    leave_approval_date: date | None = None
    medical_certificate_received: bool | None = None
    entitlement: str | None = None
    time_used: str | None = None
    medical_period_end: date | None = None
    maternity_return_date: date | None = None
    work_injury_period_end: date | None = None
    annual_carryover_deadline: date | None = None
    social_insurance_status: str | None = Field(default=None, max_length=100)
    labor_capacity_assessment: str | None = Field(default=None, max_length=40)
    return_to_work_confirmed: bool | None = None
    annual_leave_carryover: str | None = Field(default=None, max_length=40)
    unpaid_leave_compensation: str | None = Field(default=None, max_length=40)
    controlling_sources: str | None = None
    notes: str | None = None
    status: LeaveStatus | None = None


class LeaveRegistrationRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    employee_id: str | None = None
    employee_name: str | None = None
    position: str | None = None
    jurisdiction: str
    leave_type: LeaveType
    leave_start: date
    expected_return: date | None = None
    intermittent: bool = False
    accumulated_work_years: int | None = None
    company_work_years: int | None = None
    normal_schedule: str | None = None
    leave_approved: bool = False
    leave_approval_date: date | None = None
    medical_certificate_received: bool = False
    entitlement: str | None = None
    time_used: str | None = None
    medical_period_end: date | None = None
    maternity_return_date: date | None = None
    work_injury_period_end: date | None = None
    annual_carryover_deadline: date | None = None
    social_insurance_status: str | None = None
    labor_capacity_assessment: str | None = None
    return_to_work_confirmed: bool = False
    annual_leave_carryover: str | None = None
    unpaid_leave_compensation: str | None = None
    controlling_sources: str | None = None
    notes: str | None = None
    status: LeaveStatus = "active"
    last_updated: date | None = None


class LeaveRegistrationList(BaseSchema):
    items: list[LeaveRegistrationRead]
    total: int
