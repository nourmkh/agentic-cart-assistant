from typing import Any, Dict, List, Optional

import httpx


class PinterestAPIService:
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self.base_url = "https://api.pinterest.com/v5"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    def get_user_account(self) -> Dict[str, Any]:
        return self._get("/user_account")

    def get_boards(self) -> List[Dict[str, Any]]:
        data = self._get("/boards", params={"page_size": 25})
        return data.get("items") or data.get("data") or []

    def get_board_pins(self, board_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        data = self._get(
            f"/boards/{board_id}/pins",
            params={"page_size": limit},
        )
        return data.get("items") or data.get("data") or []


def extract_pin_image_url(pin: Dict[str, Any]) -> Optional[str]:
    media = pin.get("media") or {}
    images = media.get("images") or {}
    if isinstance(images, dict) and images:
        if "original" in images and isinstance(images["original"], dict):
            return images["original"].get("url")
        # Fallback to any image size
        for value in images.values():
            if isinstance(value, dict) and value.get("url"):
                return value.get("url")
    return None
