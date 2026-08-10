import secrets, hashlib, base64

from sesc_auth_sdk.services import JWKSManager


class SecretsGenerator:
    @staticmethod
    def generate_pkce() -> tuple[str, str]:
        code_verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(code_verifier.encode()).digest()
        return code_verifier, (
            base64.urlsafe_b64encode(digest)
            .decode()
            .rstrip("=")
        )

    @staticmethod
    def generate_secret_string() -> str:
        return secrets.token_urlsafe(32)

__all__ = ["SecretsGenerator"]
