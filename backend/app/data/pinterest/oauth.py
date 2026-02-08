from typing import Dict, Any
from urllib.parse import urlencode

import httpx

from .config import PinterestConfig


class PinterestOAuthService:
    @staticmethod
    def get_oauth_url(state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": PinterestConfig.PINTEREST_APP_ID,
            "redirect_uri": PinterestConfig.PINTEREST_REDIRECT_URI,
            "state": state,
            "scope": "boards:read,pins:read,user_accounts:read",
        }
        return f"{PinterestConfig.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    @staticmethod
    def exchange_code_for_token(code: str) -> Dict[str, Any]:
        token_url = "https://api.pinterest.com/v5/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": PinterestConfig.PINTEREST_REDIRECT_URI,
        }
        auth = httpx.BasicAuth(PinterestConfig.PINTEREST_APP_ID, PinterestConfig.PINTEREST_APP_SECRET)
        with httpx.Client(timeout=20) as client:
            response = client.post(token_url, data=data, auth=auth)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def fetch_user_profile(access_token: str) -> Dict[str, Any]:
        profile_url = "https://api.pinterest.com/v5/user_account"
        headers = {"Authorization": f"Bearer {access_token}"}
        with httpx.Client(timeout=20) as client:
            response = client.get(profile_url, headers=headers)
            response.raise_for_status()
            return response.json()
