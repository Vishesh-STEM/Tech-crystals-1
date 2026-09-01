"""Moodle integration service layer.

The rest of the application never imports Moodle directly - it talks to
:class:`MoodleService`. That keeps the codebase independent while making a
future Moodle deployment (web services, SSO or an LTI 1.3 launch) a matter of
implementing the methods below.

Current state: disabled by default (MOODLE_ENABLED=false) and the platform runs
with its own JWT authentication, exactly as specified for this version.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MoodleUser:
    moodle_id: int
    username: str
    email: str
    full_name: str
    roles: List[str]


class MoodleService:
    """Thin wrapper over the Moodle Web Services REST API."""

    def __init__(self, base_url: str = "", token: str = ""):
        self.base_url = (base_url or settings.MOODLE_BASE_URL).rstrip("/")
        self.token = token or settings.MOODLE_WS_TOKEN

    @property
    def enabled(self) -> bool:
        return bool(settings.MOODLE_ENABLED and self.base_url and self.token)

    # -- low level ---------------------------------------------------------
    def call(self, function: str, **params: Any) -> Any:
        if not self.enabled:
            raise RuntimeError("Moodle integration is disabled (set MOODLE_ENABLED=true).")
        payload = {
            "wstoken": self.token,
            "wsfunction": function,
            "moodlewsrestformat": "json",
            **params,
        }
        response = httpx.post(f"{self.base_url}/webservice/rest/server.php", data=payload, timeout=20.0)
        response.raise_for_status()
        return response.json()

    # -- planned integration points ---------------------------------------
    def authenticate(self, username: str, password: str) -> Optional[MoodleUser]:
        """Exchange Moodle credentials for a token, then map to a local user."""
        if not self.enabled:
            return None
        response = httpx.post(
            f"{self.base_url}/login/token.php",
            data={"username": username, "password": password, "service": "moodle_mobile_app"},
            timeout=20.0,
        )
        data = response.json()
        if "token" not in data:
            return None
        info = MoodleService(self.base_url, data["token"]).call("core_webservice_get_site_info")
        return MoodleUser(
            moodle_id=info.get("userid", 0),
            username=info.get("username", username),
            email=info.get("useremail", ""),
            full_name=info.get("fullname", username),
            roles=["student"],
        )

    def list_courses(self) -> List[Dict[str, Any]]:
        return self.call("core_course_get_courses") if self.enabled else []

    def sync_grade(self, moodle_user_id: int, course_id: int, item_name: str, grade: float) -> bool:
        """Push a Vidyalaya AI quiz result back to the Moodle gradebook."""
        if not self.enabled:
            logger.debug("Moodle disabled - grade sync skipped (%s: %s)", item_name, grade)
            return False
        self.call(
            "core_grades_update_grades",
            source="vidyalaya_ai",
            courseid=course_id,
            component="mod_assign",
            activityid=0,
            itemnumber=0,
            **{"grades[0][studentid]": moodle_user_id, "grades[0][grade]": grade},
        )
        return True

    # -- LTI ---------------------------------------------------------------
    def lti_launch_claims(self, user_id: int, resource_link_id: str) -> Dict[str, Any]:
        """Minimal LTI 1.3 claim set used when Vidyalaya AI is launched as a tool."""
        return {
            "iss": settings.MOODLE_BASE_URL,
            "aud": settings.MOODLE_LTI_CLIENT_ID,
            "sub": str(user_id),
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
            "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": {"id": resource_link_id},
            "https://purl.imsglobal.org/spec/lti/claim/roles": [
                "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
            ],
        }


def get_moodle_service() -> MoodleService:
    return MoodleService()


def integration_status() -> Dict[str, Any]:
    service = get_moodle_service()
    return {
        "enabled": service.enabled,
        "base_url": service.base_url or None,
        "capabilities": {
            "authentication": "planned - MoodleService.authenticate()",
            "web_services": "planned - MoodleService.call()",
            "grade_sync": "planned - MoodleService.sync_grade()",
            "lti_1_3": "planned - MoodleService.lti_launch_claims()",
        },
        "note": (
            "Standalone JWT authentication is active. No application code depends on Moodle; "
            "enable MOODLE_ENABLED and fill in the service layer to connect an LMS."
        ),
    }
