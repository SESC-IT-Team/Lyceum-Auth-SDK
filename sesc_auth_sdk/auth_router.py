

from fastapi import APIRouter, Response, Request, HTTPException, status

from sesc_auth_sdk.config import settings
from sesc_auth_sdk.schemas.token import AuthentikTokenResponse, TokenResponse, TokenRequest, LogoutResponse
from sesc_auth_sdk.schemas.authorization_url_response import AuthorizationUrlResponse
from sesc_auth_sdk.services.requests_service import RequestsService
from sesc_auth_sdk.services.secrets_generator import SecretsGenerator

router = APIRouter(prefix="/auth")

REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_grant", "error_description": "The provided authorization code, state or code_verifier is invalid, expired, or revoked."})
REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_grant", "error_description": "The provided refresh_token is invalid, expired, or revoked."})
GRANT_TYPE_NOT_SUPPORTED_EXCEPTION = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "unsupported_grant_type", "error_description": "The authorization grant type is not supported by the authorization server."})

def _set_initial_oauth_code_flow_cookies(response: Response, state: str, code_verifier: str):
    response.set_cookie(key='oauth_code_verifier',
                        value=code_verifier,
                        # domain=settings.cookie_domain,
                        secure=settings.cookie_secure,
                        samesite=settings.cookie_samesite,
                        httponly=True,
                        path='/auth',
                        max_age=300)
    response.set_cookie(key='oauth_state',
                        value=state,
                        # domain=settings.cookie_domain,
                        secure=settings.cookie_secure,
                        samesite=settings.cookie_samesite,
                        httponly=True,
                        path='/auth',
                        max_age=300)

def _clear_initial_oauth_code_flow_cookies(response: Response):
    response.delete_cookie(key='oauth_code_verifier', path='/auth')
    response.delete_cookie(key='oauth_state', path='/auth')

def _set_refresh_token_cookie(response: Response, refresh_token: str):
    response.set_cookie(key='refresh_token',
                        value=refresh_token,
                        # domain=settings.cookie_domain,
                        secure=settings.cookie_secure,
                        samesite=settings.cookie_samesite,
                        httponly=True,
                        path='/auth',
                        max_age=settings.refresh_token_ttl)

def _clear_refresh_token_cookie(response: Response):
    response.delete_cookie(key='refresh_token', path='/auth')

@router.post("/login")
def login(response: Response, scope: str) -> AuthorizationUrlResponse:
    code_verifier, code_challenge = SecretsGenerator.generate_pkce()
    state = SecretsGenerator.generate_state()
    print(f'{settings.cookie_domain=}')
    print(f'{settings.cookie_secure=}')
    url = f'{settings.authentik_url}/application/o/authorize/?response_type=code&client_id={settings.client_id}&scope={scope}&code_challenge={code_challenge}&code_challenge_method=S256&state={state}&redirect_uri={settings.login_redirect_uri}'
    _set_initial_oauth_code_flow_cookies(response, state, code_verifier)
    return AuthorizationUrlResponse(authorization_url=url)

@router.post("/token")
async def token(body: TokenRequest, request: Request, response: Response) -> TokenResponse:
    if body.grant_type == 'authorization_code':
        cookie_state = request.cookies.get('oauth_state')
        print(f'{cookie_state=}')
        cookie_code_verifier = request.cookies.get('oauth_code_verifier')
        print(f'{cookie_code_verifier=}')
        _clear_initial_oauth_code_flow_cookies(response)
        if not cookie_code_verifier or not cookie_state or not body.code or not body.state or body.state != cookie_state:
            raise REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION
        try:
            token_response = AuthentikTokenResponse(**(await RequestsService.exchange_code(body.code, cookie_code_verifier)))
            if token_response.refresh_token:
                _set_refresh_token_cookie(response, token_response.refresh_token)
            return TokenResponse(**token_response.model_dump())
        except Exception as e:
            print(e)
            raise REJECT_EXCHANGE_CODE_REQUEST_EXCEPTION
    elif body.grant_type == 'refresh_token':
        refresh_token = request.cookies.get('refresh_token')
        if not refresh_token:
            raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION
        try:
            token_response = AuthentikTokenResponse(**(await RequestsService.refresh_token(refresh_token)))
            _set_refresh_token_cookie(response, token_response.refresh_token)
            return TokenResponse(**token_response.model_dump())
        except Exception:
            raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION
    else:
        raise GRANT_TYPE_NOT_SUPPORTED_EXCEPTION


@router.post('/logout')
def logout(request: Request, response: Response) -> LogoutResponse:
    refresh_token = request.cookies.get('refresh_token')
    _clear_refresh_token_cookie(response)
    if not refresh_token:
        raise REJECT_REFRESH_TOKEN_REQUEST_EXCEPTION
    try:
        RequestsService.revoke_refresh_token(refresh_token)
    except Exception:
        return LogoutResponse(refresh_token_revoked=False)
    return LogoutResponse(refresh_token_revoked=True)

