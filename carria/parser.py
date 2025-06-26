import asyncio
import logging
import functools as ft

import bs4

from . import utils
from . import models
from . import client

logger = logging.getLogger(__name__)

async def _get_all_sections(
    url: str,
    http_client: client.HTTPClient,
    delay: int,
    starting_page: int,
) -> list[bs4.element.Tag]:
    all_sections = []
    current_page = starting_page
    while True:
        logger.debug(f"Current page: {current_page}")
        url = utils.get_page_url(url, current_page)
        result = await utils.retry_func(ft.partial(http_client.make_get_request, url))
        html = bs4.BeautifulSoup(result, "html.parser")
        sections = html.find("div", id="searchResults").find_all("section", class_="ticket-item")
        if len(sections) == 0:
            logger.debug("No sections left")
            break
            
        current_page += 1
        all_sections.extend(sections)
        await asyncio.sleep(delay / 1000)
    return all_sections

async def parse_all(url, delay: int=800, starting_page: int=0) -> list[models.CarInfo]:
    http_client = client.HTTPClient()
    sections = await _get_all_sections(url, http_client, delay, starting_page)
    return [utils.get_car_info(s) for s in sections]