from sesc_auth_sdk.settings.base_settings import Settings


class M2MSettings(Settings):
    authentik_url: str
    client_id: str
    application_slug: str
    service_account_username: str
    service_account_app_password: str
    scope: str = ""

    @property
    def issuer(self) -> str:
        return f'{self.authentik_url}/application/o/{self.application_slug}/'
