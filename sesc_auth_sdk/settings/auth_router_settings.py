from typing import Literal

from sesc_auth_sdk.settings.base_settings import Settings


class AuthRouterSettings(Settings):
    authentik_url: str
    internal_authentik_url: str
    client_id: str
    client_secret: str
    application_slug: str
    login_redirect_uri: str
    router_path: str

    cookie_domain: str | None = None
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] | None = None

    refresh_token_ttl: int = 2592000  # 30 days
    access_token_ttl: int = 300  # 5 mins
    oauth_initial_oauth_code_flow_cookies_ttl: int = 300  # 5 mins
    send_access_token_in_json_response: bool = True
    send_access_token_as_cookie: bool = False
