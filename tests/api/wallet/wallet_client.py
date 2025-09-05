import httpx


class WalletClient:
    def __init__(self, base_url: str = "http://localhost:3005"):
        self.base_url = base_url

    async def get_user_wallet(self, token: str) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/wallet"
            headers = {}
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            return await client.get(url, headers=headers)

    async def wallet_deposit(self, token: str, amount: float) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/wallet/deposit"
            headers = {}
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            req = {"amount": amount}
            return await client.post(url, headers=headers, json=req)
