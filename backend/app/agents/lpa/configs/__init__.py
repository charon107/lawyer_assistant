"""Document type configuration registry.

Each sub-module exports a CONFIG dict with type-specific settings.
This module assembles them into DOCUMENT_TYPE_CONFIGS with shared defaults.
"""

from app.agents.lpa import prompts_dir as _get_prompts_dir
from app.agents.lpa.configs.articles_of_association import CONFIG as ARTICLES_OF_ASSOCIATION_CONFIG
from app.agents.lpa.configs.construction import CONFIG as CONSTRUCTION_CONFIG
from app.agents.lpa.configs.contract import CONFIG as CONTRACT_CONFIG
from app.agents.lpa.configs.employment import CONFIG as EMPLOYMENT_CONFIG
from app.agents.lpa.configs.equity_investment import CONFIG as EQUITY_INVESTMENT_CONFIG
from app.agents.lpa.configs.ip_license import CONFIG as IP_LICENSE_CONFIG
from app.agents.lpa.configs.lease import CONFIG as LEASE_CONFIG
from app.agents.lpa.configs.loan import CONFIG as LOAN_CONFIG
from app.agents.lpa.configs.lpa import CONFIG as LPA_CONFIG
from app.agents.lpa.configs.marital_property import CONFIG as MARITAL_PROPERTY_CONFIG
from app.agents.lpa.configs.nda import CONFIG as NDA_CONFIG
from app.agents.lpa.configs.sales import CONFIG as SALES_CONFIG
from app.agents.lpa.configs.service import CONFIG as SERVICE_CONFIG
from app.agents.lpa.configs.will_estate import CONFIG as WILL_ESTATE_CONFIG

PROMPTS_DIR = _get_prompts_dir()

_DEFAULT_PROMPT_TEMPLATES = {
    "chapter_split": str(PROMPTS_DIR / "chapter_split.md"),
    "fact_labeling": str(PROMPTS_DIR / "fact_labeling.md"),
    "simple_review": str(PROMPTS_DIR / "simple_review.md"),
    "complex_review": str(PROMPTS_DIR / "complex_review.md"),
    "cross_check": str(PROMPTS_DIR / "cross_check.md"),
}

_RAW_CONFIGS = {
    "lpa": LPA_CONFIG,
    "contract": CONTRACT_CONFIG,
    "nda": NDA_CONFIG,
    "employment": EMPLOYMENT_CONFIG,
    "lease": LEASE_CONFIG,
    "loan": LOAN_CONFIG,
    "sales": SALES_CONFIG,
    "service": SERVICE_CONFIG,
    "ip_license": IP_LICENSE_CONFIG,
    "equity_investment": EQUITY_INVESTMENT_CONFIG,
    "construction": CONSTRUCTION_CONFIG,
    "articles_of_association": ARTICLES_OF_ASSOCIATION_CONFIG,
    "marital_property": MARITAL_PROPERTY_CONFIG,
    "will_estate": WILL_ESTATE_CONFIG,
}

DOCUMENT_TYPE_CONFIGS: dict[str, dict] = {}
for _key, _cfg in _RAW_CONFIGS.items():
    DOCUMENT_TYPE_CONFIGS[_key] = {
        **_cfg,
        "prompt_templates": _cfg.get("prompt_templates", _DEFAULT_PROMPT_TEMPLATES),
    }
