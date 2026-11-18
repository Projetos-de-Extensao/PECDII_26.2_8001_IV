from .settings import *  # noqa: F403

ROOT_URLCONF = "project.urls_portal"
LOGIN_URL = "portal_login"
LOGIN_REDIRECT_URL = "portal"
LOGOUT_REDIRECT_URL = "portal_login"
SESSION_COOKIE_NAME = "playmakerz_portal_session"
CSRF_COOKIE_NAME = "playmakerz_portal_csrf"
