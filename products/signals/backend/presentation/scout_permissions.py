from typing import cast
from uuid import UUID

from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from posthog.api.routing import TeamAndOrgViewSetMixin
from posthog.auth import OAuthAccessTokenAuthentication, PersonalAPIKeyAuthentication
from posthog.permissions import is_scout_sandbox_request

from products.signals.backend.constants import SYSTEM_SCOUT_NAMES
from products.signals.backend.models import SignalScoutConfig, SignalScoutNote, SignalScoutRun


def can_read_system_scouts(request: Request) -> bool:
    return bool(request.user.is_staff or is_scout_sandbox_request(request))


class SystemScoutAccessPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if can_read_system_scouts(request):
            return True
        team_view = cast(TeamAndOrgViewSetMixin, view)
        team_id = team_view.team.parent_team_id or team_view.team.id
        supplied = request.data.get("skill_name") if isinstance(request.data, dict) else None
        if (isinstance(supplied, str) and supplied in SYSTEM_SCOUT_NAMES) or request.query_params.get(
            "skill_name"
        ) in SYSTEM_SCOUT_NAMES:
            raise NotFound()
        run_ids = request.data.get("run_ids") if isinstance(request.data, dict) else None
        if isinstance(run_ids, list):
            try:
                identifiers = [UUID(str(value)) for value in run_ids]
            except ValueError:
                identifiers = []
            if (
                SignalScoutRun.objects.for_team(team_id)
                .filter(id__in=identifiers, skill_name__in=SYSTEM_SCOUT_NAMES)
                .exists()
            ):
                raise NotFound()
        identifier = view.kwargs.get("run_id") or view.kwargs.get("id")
        if identifier:
            try:
                identifier = UUID(str(identifier))
            except ValueError:
                return True
            for model in (SignalScoutConfig, SignalScoutRun, SignalScoutNote):
                if model.objects.for_team(team_id).filter(id=identifier, skill_name__in=SYSTEM_SCOUT_NAMES).exists():
                    raise NotFound()
        return True


class ScoutCanonicalTeamAccessPermission(BasePermission):
    """Authorize requests against the project that owns the scout data."""

    message = "You don't have access to the project that owns this data."

    def has_permission(self, request: Request, view: APIView) -> bool:
        team_view = cast(TeamAndOrgViewSetMixin, view)
        if not request.user.is_authenticated:
            # Unreachable while `IsAuthenticated` runs ahead of this class, but deny rather than
            # allow, so this class can never be the reason an anonymous request gets through.
            return False
        team = team_view.team
        if team.parent_team_id is None or team.parent_team_id == team.id or team.parent_team is None:
            return True
        authenticator = request.successful_authenticator
        scoped_teams = None
        if isinstance(authenticator, OAuthAccessTokenAuthentication):
            scoped_teams = authenticator.access_token.scoped_teams
        elif isinstance(authenticator, PersonalAPIKeyAuthentication):
            scoped_teams = authenticator.personal_api_key.scoped_teams
        if scoped_teams and team.parent_team_id not in scoped_teams:
            return False
        level = team_view.user_permissions.team(team.parent_team).effective_membership_level
        return level is not None
