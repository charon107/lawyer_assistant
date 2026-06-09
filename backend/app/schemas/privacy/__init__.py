"""Privacy-legal Pydantic schemas."""

from app.schemas.privacy.cold_start import ColdStartRequest, ColdStartResponse, ColdStartStep
from app.schemas.privacy.dsar import (
    PrivacyDsarCreate,
    PrivacyDsarList,
    PrivacyDsarRead,
    PrivacyDsarUpdate,
)
from app.schemas.privacy.notification import (
    PrivacyNotificationList,
    PrivacyNotificationRead,
)
from app.schemas.privacy.profile import (
    PrivacyModuleStatusResponse,
    PrivacyProfileCreate,
    PrivacyProfileRead,
    PrivacyProfileUpdate,
)
from app.schemas.privacy.review import (
    PrivacyReviewCreate,
    PrivacyReviewList,
    PrivacyReviewRead,
)

__all__ = [
    "ColdStartRequest",
    "ColdStartResponse",
    "ColdStartStep",
    "PrivacyDsarCreate",
    "PrivacyDsarList",
    "PrivacyDsarRead",
    "PrivacyDsarUpdate",
    "PrivacyModuleStatusResponse",
    "PrivacyNotificationList",
    "PrivacyNotificationRead",
    "PrivacyProfileCreate",
    "PrivacyProfileRead",
    "PrivacyProfileUpdate",
    "PrivacyReviewCreate",
    "PrivacyReviewList",
    "PrivacyReviewRead",
]
