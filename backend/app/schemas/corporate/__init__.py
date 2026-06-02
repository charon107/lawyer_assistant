"""Corporate-legal (公司并购) module schemas."""

# ruff: noqa: RUF022 - __all__ grouped by entity for readability

from app.schemas.corporate.checklist import (
    ClosingChecklistItemCreate,
    ClosingChecklistItemList,
    ClosingChecklistItemRead,
    ClosingChecklistItemUpdate,
)
from app.schemas.corporate.deal import (
    CorporateDealCreate,
    CorporateDealList,
    CorporateDealRead,
    CorporateDealUpdate,
)
from app.schemas.corporate.diligence import (
    DiligenceIssueCreate,
    DiligenceIssueList,
    DiligenceIssueRead,
    DiligenceIssueUpdate,
)
from app.schemas.corporate.entity import (
    CorporateEntityCreate,
    CorporateEntityList,
    CorporateEntityRead,
    CorporateEntityUpdate,
    EntityComplianceItemCreate,
    EntityComplianceItemList,
    EntityComplianceItemRead,
    EntityComplianceItemUpdate,
)
from app.schemas.corporate.governance import (
    BoardDocumentCreate,
    BoardDocumentList,
    BoardDocumentRead,
    BoardDocumentUpdate,
    BoardMeetingCreate,
    BoardMeetingList,
    BoardMeetingRead,
)
from app.schemas.corporate.integration import (
    IntegrationTaskCreate,
    IntegrationTaskList,
    IntegrationTaskRead,
    IntegrationTaskUpdate,
)
from app.schemas.corporate.material_contract import (
    MaterialContractItemCreate,
    MaterialContractItemList,
    MaterialContractItemRead,
    MaterialContractItemUpdate,
)
from app.schemas.corporate.notification import (
    CorporateNotificationList,
    CorporateNotificationRead,
)
from app.schemas.corporate.profile import (
    CorporateModule,
    CorporateProfileCreate,
    CorporateProfileRead,
    CorporateProfileUpdate,
    ModuleStatus,
    SetupDepth,
    UsedBy,
)
from app.schemas.corporate.tabular import (
    TabularColumn,
    TabularReviewCreate,
    TabularReviewList,
    TabularReviewRead,
    TabularReviewUpdate,
)
from app.schemas.corporate.vdr import (
    VdrDocumentCreate,
    VdrDocumentList,
    VdrDocumentRead,
    VdrDocumentUpdate,
)

__all__ = [
    # profile
    "CorporateModule",
    "CorporateProfileCreate",
    "CorporateProfileRead",
    "CorporateProfileUpdate",
    "ModuleStatus",
    "SetupDepth",
    "UsedBy",
    # deal
    "CorporateDealCreate",
    "CorporateDealList",
    "CorporateDealRead",
    "CorporateDealUpdate",
    # vdr
    "VdrDocumentCreate",
    "VdrDocumentList",
    "VdrDocumentRead",
    "VdrDocumentUpdate",
    # diligence
    "DiligenceIssueCreate",
    "DiligenceIssueList",
    "DiligenceIssueRead",
    "DiligenceIssueUpdate",
    # tabular
    "TabularColumn",
    "TabularReviewCreate",
    "TabularReviewList",
    "TabularReviewRead",
    "TabularReviewUpdate",
    # checklist
    "ClosingChecklistItemCreate",
    "ClosingChecklistItemList",
    "ClosingChecklistItemRead",
    "ClosingChecklistItemUpdate",
    # material contracts
    "MaterialContractItemCreate",
    "MaterialContractItemList",
    "MaterialContractItemRead",
    "MaterialContractItemUpdate",
    # governance
    "BoardMeetingCreate",
    "BoardMeetingList",
    "BoardMeetingRead",
    "BoardDocumentCreate",
    "BoardDocumentList",
    "BoardDocumentRead",
    "BoardDocumentUpdate",
    # entity / compliance
    "CorporateEntityCreate",
    "CorporateEntityList",
    "CorporateEntityRead",
    "CorporateEntityUpdate",
    "EntityComplianceItemCreate",
    "EntityComplianceItemList",
    "EntityComplianceItemRead",
    "EntityComplianceItemUpdate",
    # integration
    "IntegrationTaskCreate",
    "IntegrationTaskList",
    "IntegrationTaskRead",
    "IntegrationTaskUpdate",
    # notifications
    "CorporateNotificationList",
    "CorporateNotificationRead",
]
