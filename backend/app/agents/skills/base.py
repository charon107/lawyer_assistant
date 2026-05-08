"""Base class for legal domain skills — lawyer persona methodology."""

from dataclasses import dataclass


@dataclass
class LegalDomainSkill:
    """A domain-expert lawyer persona.

    Captures HOW a specialist lawyer thinks about problems in their domain,
    written as flowing guidance — a senior lawyer mentoring a junior.
    Not lists, not enumeration. Methodology.
    """

    name: str
    category: str
    guidance: str

    def to_prompt(self) -> str:
        return f"## {self.name}\n\n{self.guidance}"
