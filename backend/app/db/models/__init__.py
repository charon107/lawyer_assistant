"""Database models."""

# ruff: noqa: I001, RUF022 - Imports structured for Jinja2 template conditionals
from app.db.models.user import User
from app.db.models.user_llm_config import UserLLMConfig
from app.db.models.conversation import Conversation, Message, ToolCall
from app.db.models.chat_file import ChatFile
from app.db.models.message_rating import MessageRating
from app.db.models.conversation_share import ConversationShare
from app.db.models.law_metadata import LawMetadata
from app.db.models.system_log import SystemLog
from app.db.models.commercial_profile import CommercialProfile
from app.db.models.contract_review import ContractReview
from app.db.models.module_config import ModuleConfig
from app.db.models.commercial_matter import CommercialMatter
from app.db.models.renewal_registration import RenewalRegistration
from app.db.models.contract_deviation import ContractDeviation
from app.db.models.playbook_proposal import PlaybookProposal
from app.db.models.commercial_notification import CommercialNotification
from app.db.models.corporate_profile import CorporateProfile
from app.db.models.corporate_deal import CorporateDeal
from app.db.models.vdr_document import VdrDocument
from app.db.models.diligence_issue import DiligenceIssue
from app.db.models.tabular_review import TabularReview
from app.db.models.closing_checklist_item import ClosingChecklistItem
from app.db.models.material_contract_item import MaterialContractItem
from app.db.models.board_meeting import BoardMeeting, BoardDocument
from app.db.models.corporate_entity import CorporateEntity, EntityComplianceItem
from app.db.models.integration_task import IntegrationTask
from app.db.models.corporate_notification import CorporateNotification
from app.db.models.employment_profile import EmploymentProfile
from app.db.models.leave_registration import LeaveRegistration
from app.db.models.employment_review import EmploymentReview
from app.db.models.employment_investigation import (
    EmploymentInvestigation,
    InvestigationLogEntry,
    InvestigationSource,
    InvestigationGap,
)
from app.db.models.employment_expansion import EmploymentExpansion
from app.db.models.employment_notification import EmploymentNotification
from app.db.models.privacy_profile import PrivacyProfile
from app.db.models.privacy_review import PrivacyReview
from app.db.models.privacy_dsar import PrivacyDsar
from app.db.models.privacy_notification import PrivacyNotification

__all__ = [
    "User",
    "UserLLMConfig",
    "Conversation",
    "Message",
    "ToolCall",
    "ChatFile",
    "MessageRating",
    "ConversationShare",
    "LawMetadata",
    "SystemLog",
    "CommercialProfile",
    "ContractReview",
    "ModuleConfig",
    "CommercialMatter",
    "RenewalRegistration",
    "ContractDeviation",
    "PlaybookProposal",
    "CommercialNotification",
    "CorporateProfile",
    "CorporateDeal",
    "VdrDocument",
    "DiligenceIssue",
    "TabularReview",
    "ClosingChecklistItem",
    "MaterialContractItem",
    "BoardMeeting",
    "BoardDocument",
    "CorporateEntity",
    "EntityComplianceItem",
    "IntegrationTask",
    "CorporateNotification",
    "EmploymentProfile",
    "LeaveRegistration",
    "EmploymentReview",
    "EmploymentInvestigation",
    "InvestigationLogEntry",
    "InvestigationSource",
    "InvestigationGap",
    "EmploymentExpansion",
    "EmploymentNotification",
    "PrivacyProfile",
    "PrivacyReview",
    "PrivacyDsar",
    "PrivacyNotification",
]
