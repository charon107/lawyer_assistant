"""Document type configurations for the review pipeline.

Each document type defines its own:
- chapter_keywords: keywords for chapter boundary detection
- entity_patterns: regex patterns for entity extraction
- fact_tool_schema: JSON Schema for the LLM fact-labeling tool
- risk_rules: dict of review rules
- rule_keyword_map: mapping from rule IDs to keywords for complexity classification
- simple_rule_ids / complex_rule_ids: rule ID sets for fast vs deep review
- prompt_templates: paths to prompt template files per stage

Individual configs live in configs/ sub-package.
"""

from app.agents.lpa.configs import DOCUMENT_TYPE_CONFIGS

__all__ = ["DOCUMENT_TYPE_CONFIGS", "get_document_type_config"]


def get_document_type_config(document_type: str) -> dict:
    """Get configuration for a document type.

    Args:
        document_type: The document type key.

    Returns:
        Configuration dict for the given document type.

    Raises:
        KeyError: If the document type is not registered.
    """
    if document_type not in DOCUMENT_TYPE_CONFIGS:
        raise KeyError(
            f"Unknown document type: {document_type}. Available: {list(DOCUMENT_TYPE_CONFIGS.keys())}"
        )
    return DOCUMENT_TYPE_CONFIGS[document_type]
