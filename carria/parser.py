import functools as ft
import logging
from typing import AsyncGenerator

import bs4

from . import client, models, utils

logger = logging.getLogger(__name__)
    
async def _get_sections(url: str) -> list[models.CarInfo]:
    http_client = client.HTTPClient()
    html_page = await utils.retry_func(ft.partial(http_client.make_get_request, url))
    html = bs4.BeautifulSoup(html_page, "html.parser")
    sections = html.find("div", id="searchResults").find_all("section", class_="ticket-item")
    return sections

async def parse_page(url: str, page: int) -> AsyncGenerator[list[models.CarInfo], None]:
    url = utils.get_page_url(url, page) 
    sections = await _get_sections(url)
    return [utils.get_car_info(s) for s in sections]

async def parse_total_expected(url: str) -> int:
    http_client = client.HTTPClient()
    html_page = await utils.retry_func(ft.partial(http_client.make_get_request, url))
    html = bs4.BeautifulSoup(html_page, "html.parser")
    return utils.get_total_expected_cars(html)