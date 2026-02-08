from urllib.parse import urlencode
from .config import PinterestConfig


class PinterestOAuthService:
    @staticmethod
    def get_oauth_url(state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": PinterestConfig.PINTEREST_APP_ID,
            "redirect_uri": PinterestConfig.PINTEREST_REDIRECT_URI,
            "state": state,
            "scope": "boards:read,pins:read",
        }
        return f"{PinterestConfig.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
