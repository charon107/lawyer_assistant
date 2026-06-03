"""Employment-legal (劳动用工) agent module."""

from app.agents.employment.agent import EmploymentSkillName, create_employment_agent
from app.agents.employment.deps import EmploymentDeps

__all__ = ["EmploymentDeps", "EmploymentSkillName", "create_employment_agent"]
