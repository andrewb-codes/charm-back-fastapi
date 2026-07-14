from enum import StrEnum


class RateLimitScope(StrEnum):
    LOGIN_ACCOUNT = "login_account"
    LOGIN_GLOBAL = "login_global"
    REGISTER_IDENTIFIER = "register_identifier"
    REGISTER_GLOBAL = "register_global"
    PROFILE_READ = "profile_read"
    PROFILE_WRITE = "profile_write"
    CHARM_READ = "charm_read"
    CHARM_REACT = "charm_react"
    MATCHES_READ = "matches_read"
    ADMIN_READ = "admin_read"
    ADMIN_WRITE = "admin_write"
