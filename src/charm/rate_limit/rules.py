from dataclasses import dataclass
from typing import Literal

from charm.rate_limit.scopes import RateLimitScope

RateLimitFailureMode = Literal["open", "closed"]


@dataclass(frozen=True)
class RateLimitRule:
    scope: RateLimitScope
    limit: str
    failure_mode: RateLimitFailureMode = "open"


REGISTER_IDENTIFIER_LIMIT = RateLimitRule(
    scope=RateLimitScope.REGISTER_IDENTIFIER,
    limit="3 per hour",
    failure_mode="open",
)

REGISTER_GLOBAL_LIMIT = RateLimitRule(
    scope=RateLimitScope.REGISTER_GLOBAL,
    limit="30 per hour",
    failure_mode="open",
)

LOGIN_ACCOUNT_LIMIT = RateLimitRule(
    scope=RateLimitScope.LOGIN_ACCOUNT,
    limit="5 per minute",
    failure_mode="open",
)

LOGIN_GLOBAL_LIMIT = RateLimitRule(
    scope=RateLimitScope.LOGIN_GLOBAL,
    limit="60 per minute",
    failure_mode="open",
)

PROFILE_READ_LIMIT = RateLimitRule(
    scope=RateLimitScope.PROFILE_READ,
    limit="120 per minute",
    failure_mode="open",
)

PROFILE_WRITE_LIMIT = RateLimitRule(
    scope=RateLimitScope.PROFILE_WRITE,
    limit="30 per minute",
    failure_mode="open",
)

CHARM_READ_LIMIT = RateLimitRule(
    scope=RateLimitScope.CHARM_READ,
    limit="60 per minute",
    failure_mode="open",
)

CHARM_REACT_LIMIT = RateLimitRule(
    scope=RateLimitScope.CHARM_REACT,
    limit="60 per minute",
    failure_mode="open",
)

MATCHES_READ_LIMIT = RateLimitRule(
    scope=RateLimitScope.MATCHES_READ,
    limit="60 per minute",
    failure_mode="open",
)

ADMIN_READ_LIMIT = RateLimitRule(
    scope=RateLimitScope.ADMIN_READ,
    limit="120 per minute",
    failure_mode="open",
)

ADMIN_WRITE_LIMIT = RateLimitRule(
    scope=RateLimitScope.ADMIN_WRITE,
    limit="30 per minute",
    failure_mode="open",
)
