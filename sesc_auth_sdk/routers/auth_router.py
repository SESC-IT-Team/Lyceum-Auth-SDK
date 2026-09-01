import logging

from fastapi import APIRouter, Response, Request, HTTPException, status, Query

from sesc_auth_sdk.settings.auth_router_settings import AuthRouterSettings
from sesc_auth_sdk.schemas.token import TokenResponse, AuthentikTokenResponse, LogoutResponse, ExchangeCodeRequest
from sesc_auth_sdk.schemas.authorization_url_response import AuthorizationUrlResponse
from sesc_auth_sdk.services.jwks_manager import JWKSManager

from sesc_auth_sdk.services.requests_service import RequestsService
from sesc_auth_sdk.services.secrets_generator import SecretsGenerator
from sesc_auth_sdk.settings import TokenValidationSettings

REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_grant", "error_description": "The provided authorization code, state, nonce or code_verifier is invalid, expired, or revoked."})
REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_grant", "error_description": "The provided refresh_token is invalid, expired, or revoked."})
GRANT_TYPE_NOT_SUPPORTED_EXCEPTION = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "unsupported_grant_type", "error_description": "The authorization grant type is not supported by the authorization server."})

logger = logging.getLogger(__name__)

def create_auth_router(settings: AuthRouterSettings) -> APIRouter:
    jwks_manager = JWKSManager(TokenValidationSettings(allowed_application_slugs=[settings.application_slug], internal_authentik_url=settings.internal_authentik_url))
    router = APIRouter()

    def _generate_end_session_url(next_: str | None) -> str:
        url = f'{settings.authentik_url}/application/o/{settings.application_slug}/end-session/'
        if next_:
            url += f'?next={next_}'
        return url

    def _generate_authorization_url(scope: str, code_challenge: str, state: str, nonce: str) -> str:
        return f'{settings.authentik_url}/application/o/authorize/?response_type=code&client_id={settings.client_id}&scope={scope}&code_challenge={code_challenge}&code_challenge_method=S256&state={state}&nonce={nonce}&redirect_uri={settings.login_redirect_uri}'

    def _set_initial_oauth_code_flow_cookies(response: Response, state: str, code_verifier: str, nonce: str):
        response.set_cookie(key='oauth_code_verifier',
                            value=code_verifier,
                            domain=settings.cookie_domain,
                            secure=settings.cookie_secure,
                            samesite=settings.cookie_samesite,
                            httponly=True,
                            path=settings.router_path,
                            max_age=settings.oauth_initial_oauth_code_flow_cookies_ttl)
        response.set_cookie(key='oauth_state',
                            value=state,
                            domain=settings.cookie_domain,
                            secure=settings.cookie_secure,
                            samesite=settings.cookie_samesite,
                            httponly=True,
                            path=settings.router_path,
                            max_age=settings.oauth_initial_oauth_code_flow_cookies_ttl)
        response.set_cookie(key='oauth_nonce',
                            value=nonce,
                            domain=settings.cookie_domain,
                            secure=settings.cookie_secure,
                            samesite=settings.cookie_samesite,
                            httponly=True,
                            path=settings.router_path,
                            max_age=settings.oauth_initial_oauth_code_flow_cookies_ttl)

    def _clear_initial_oauth_code_flow_cookies(response: Response):
        response.delete_cookie(key='oauth_code_verifier', path=settings.router_path)
        response.delete_cookie(key='oauth_state', path=settings.router_path)
        response.delete_cookie(key='oauth_nonce', path=settings.router_path)

    def _set_refresh_token_cookie(response: Response, refresh_token: str):
        response.set_cookie(key='refresh_token',
                            value=refresh_token,
                            domain=settings.cookie_domain,
                            secure=settings.cookie_secure,
                            samesite=settings.cookie_samesite,
                            httponly=True,
                            path=settings.router_path,
                            max_age=settings.refresh_token_ttl)

    def _set_access_token_cookie(response: Response, access_token: str):
        response.set_cookie(key='access_token',
                            value=access_token,
                            domain=settings.cookie_domain,
                            secure=settings.cookie_secure,
                            samesite=settings.cookie_samesite,
                            httponly=True,
                            path='/',
                            max_age=settings.access_token_ttl)

    def _clear_refresh_token_cookie(response: Response):
        response.delete_cookie(key='refresh_token', path=settings.router_path)

    def _clear_access_token_cookie(response: Response):
        response.delete_cookie(key='access_token', path='/')

    def _construct_token_response(response: Response, token_response: AuthentikTokenResponse) -> TokenResponse:
        res = TokenResponse(token_type=token_response.token_type, scope=token_response.scope,
                            expires_in=token_response.expires_in, id_token=token_response.id_token)
        if settings.send_access_token_in_json_response:
            res.access_token = token_response.access_token
        if token_response.refresh_token:
            _set_refresh_token_cookie(response, token_response.refresh_token)
        if settings.send_access_token_as_cookie:
            _set_access_token_cookie(response, token_response.access_token)
        else:
            _clear_access_token_cookie(response)
        return res

    @router.post("/login")
    def login(response: Response, scope: str) -> AuthorizationUrlResponse:
        code_verifier, code_challenge = SecretsGenerator.generate_pkce()
        state = SecretsGenerator.generate_secret_string()
        nonce = SecretsGenerator.generate_secret_string()
        _set_initial_oauth_code_flow_cookies(response, state, code_verifier, nonce)
        return AuthorizationUrlResponse(authorization_url=_generate_authorization_url(scope, code_challenge, state, nonce))

    @router.post("/exchange_code", response_model_exclude_unset=True)
    async def exchange_code(body: ExchangeCodeRequest, request: Request, response: Response) -> TokenResponse:
        code = body.code
        state = body.state
        cookie_state = request.cookies.get('oauth_state')
        cookie_code_verifier = request.cookies.get('oauth_code_verifier')
        cookie_nonce = request.cookies.get('oauth_nonce')
        _clear_initial_oauth_code_flow_cookies(response)
        if not cookie_code_verifier or not cookie_state or not code or not state or state != cookie_state or not cookie_nonce:
            logger.warning(
                "OAuth code exchange rejected: missing or mismatched flow data "
                "(has_code=%s, has_state=%s, has_cookie_state=%s, "
                "state_matches=%s, has_code_verifier=%s, has_nonce=%s, path=%s)",
                bool(code),
                bool(state),
                bool(cookie_state),
                bool(state and cookie_state and state == cookie_state),
                bool(cookie_code_verifier),
                bool(cookie_nonce),
                request.url.path,
            )
            raise REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION
        try:
            token_response = AuthentikTokenResponse(**(await RequestsService.exchange_code(settings.internal_authentik_url, code, cookie_code_verifier,
                                                                                           settings.client_id, settings.client_secret,
                                                                                           settings.login_redirect_uri)))
            access_payload = await jwks_manager.verify_access_token(token_response.access_token)
            id_payload = await jwks_manager.verify_id_token(token_response.id_token)
            if not cookie_nonce or id_payload.nonce != cookie_nonce or access_payload.nonce != cookie_nonce:
                logger.warning(
                    "OAuth code exchange rejected: token nonce validation failed "
                    "(id_nonce_matches=%s, access_nonce_matches=%s, path=%s)",
                    bool(cookie_nonce and id_payload.nonce == cookie_nonce),
                    bool(cookie_nonce and access_payload.nonce == cookie_nonce),
                    request.url.path,
                )
                raise REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION
            return _construct_token_response(response, token_response)
        except Exception as exception:
            logger.exception(
                "OAuth code exchange failed while requesting or validating tokens "
                "(exception_type=%s, exception=%s, path=%s)",
                type(exception).__name__,
                exception,
                request.url.path,
            )
            raise REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION

    @router.post("/refresh", response_model_exclude_unset=True)
    async def refresh(request: Request, response: Response) -> TokenResponse:
        refresh_token = request.cookies.get('refresh_token')
        if not refresh_token:
            logger.warning("Refresh token request rejected: refresh token cookie is missing (path=%s)", request.url.path)
            raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION
        try:
            token_response = AuthentikTokenResponse(**(await RequestsService.refresh_token(settings.internal_authentik_url, refresh_token,
                                                                                           settings.client_id, settings.client_secret)))
            return _construct_token_response(response, token_response)
        except Exception as exception:
            logger.exception(
                "Refresh token request failed while requesting or processing tokens "
                "(exception_type=%s, exception=%s, path=%s)",
                type(exception).__name__,
                exception,
                request.url.path,
            )
            raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION


    @router.post('/logout')
    async def logout(request: Request, response: Response, next_: str | None = Query(default=None, alias='next')) -> LogoutResponse:
        refresh_token = request.cookies.get('refresh_token')
        _clear_refresh_token_cookie(response)
        _clear_access_token_cookie(response)
        if not refresh_token:
            logger.warning("Logout rejected: refresh token cookie is missing (path=%s)", request.url.path)
            raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION
        try:
            await RequestsService.revoke_refresh_token(settings.internal_authentik_url, refresh_token,
                                                       settings.client_id, settings.client_secret)
        except Exception as exception:
            logger.exception(
                "Logout failed while revoking the refresh token "
                "(exception_type=%s, exception=%s, path=%s)",
                type(exception).__name__,
                exception,
                request.url.path,
            )
            return LogoutResponse(refresh_token_revoked=False, end_session_url=_generate_end_session_url(next_))
        return LogoutResponse(refresh_token_revoked=True, end_session_url=_generate_end_session_url(next_))

    return router
