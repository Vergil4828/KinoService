from typing import Any, IO

import httpx


class UserClient:
    def __init__(self, base_url: str = "http://localhost:3005"):
        self.base_url = base_url

    async def register_user(self, user_data: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/create/user"
            return await client.post(url, json=user_data)

    async def login_user(self, credential: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/login/user"
            return await client.post(url, json=credential)

    async def get_user_data(self, token: str) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/user/data"
            headers = {}
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            return await client.get(url, headers=headers)

    async def update_user(
        self, token: str, update_data: dict[str, Any]
    ) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/update/user"
            headers = {}
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            return await client.put(url, json=update_data, headers=headers)

    async def logout_user(self, token: str) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/logout"
            headers = {}
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            return await client.post(url, headers=headers)

    async def get_new_tokens(self, refresh_token: str) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/refresh-token"
            req = {"refreshToken": refresh_token}
            return await client.post(url, json=req)

    async def upload_avatar(
        self, token: str, files: dict[str, tuple[str, bytes, str | None]]
    ) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/user/avatar"
            headers = {}
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            return await client.post(url, headers=headers, files=files)
