import httpx


class HTTPClient:
    def __init__(self, base_url: str="https://auto.ria.com/uk/"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def _make_request(
        self,
        method: str,
        url: str,
        params: dict|None=None,
        headers: dict|None=None,
        data: dict|None=None,
    ) -> dict:
        response = await self.client.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            data=data,
        )
        if response.status_code != 200:
            raise Exception(f"Request failed with status code {response.status_code}")
        return response.text
    
    async def _make_browser_request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        data: dict | None = None,
    ) -> dict:
        default_headers = {
            "Host": "auto.ria.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        combined_headers = {**default_headers, **(headers or {})}

        return await self._make_request(
            method=method,
            url=url,
            params=params,
            headers=combined_headers,
            data=data,
        )

    async def make_get_request(self, url: str):
        return await self._make_browser_request(method="GET", url=url)