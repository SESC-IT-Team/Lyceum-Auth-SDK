from fastapi import APIRouter, Response, Request, HTTPException, status

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

def create_auth_router(settings: AuthRouterSettings) -> APIRouter:
    jwks_manager = JWKSManager(TokenValidationSettings(allowed_issuers=[f'{settings.authentik_url}/application/o/{settings.application_slug}/']))
    router = APIRouter()

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
        url = f'{settings.authentik_url}/application/o/authorize/?response_type=code&client_id={settings.client_id}&scope={scope}&code_challenge={code_challenge}&code_challenge_method=S256&state={state}&nonce={nonce}&redirect_uri={settings.login_redirect_uri}'
        _set_initial_oauth_code_flow_cookies(response, state, code_verifier, nonce)
        return AuthorizationUrlResponse(authorization_url=url)

    @router.post("/exchange_code", response_model_exclude_unset=True)
    async def exchange_code(body: ExchangeCodeRequest, request: Request, response: Response) -> TokenResponse:
        code = body.code
        state = body.state
        cookie_state = request.cookies.get('oauth_state')
        cookie_code_verifier = request.cookies.get('oauth_code_verifier')
        cookie_nonce = request.cookies.get('oauth_nonce')
        _clear_initial_oauth_code_flow_cookies(response)
        if not cookie_code_verifier or not cookie_state or not code or not state or state != cookie_state or not cookie_nonce:
            raise REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION
        try:
            token_response = AuthentikTokenResponse(**(await RequestsService.exchange_code(settings.authentik_url, code, cookie_code_verifier,
                                                                                           settings.client_id, settings.client_secret,
                                                                                           settings.login_redirect_uri)))
            access_payload = await jwks_manager.verify_access_token(token_response.access_token)
            id_payload = await jwks_manager.verify_id_token(token_response.id_token)
            if not cookie_nonce or id_payload.nonce != cookie_nonce or access_payload.nonce != cookie_nonce:
                raise REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION
            return _construct_token_response(response, token_response)
        except Exception:
            raise REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION

    @router.post("/refresh", response_model_exclude_unset=True)
    async def refresh(request: Request, response: Response) -> TokenResponse:
        refresh_token = request.cookies.get('refresh_token')
        if not refresh_token:
            raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION
        try:
            token_response = AuthentikTokenResponse(**(await RequestsService.refresh_token(settings.authentik_url, refresh_token,
                                                                                           settings.client_id, settings.client_secret)))
            return _construct_token_response(response, token_response)
        except Exception:
            raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION


    @router.post('/logout')
    async def logout(request: Request, response: Response) -> LogoutResponse:
        refresh_token = request.cookies.get('refresh_token')
        _clear_refresh_token_cookie(response)
        _clear_access_token_cookie(response)
        if not refresh_token:
            raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION
        try:
            await RequestsService.revoke_refresh_token(settings.authentik_url, refresh_token,
                                                 settings.client_id, settings.client_secret)
        except Exception:
            return LogoutResponse(refresh_token_revoked=False)
        return LogoutResponse(refresh_token_revoked=True)

    return router
