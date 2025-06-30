import asyncio
import logging
import functools as ft
from typing import AsyncGenerator

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
    
async def _get_sections(url: str) -> list[models.CarInfo]:
    http_client = client.HTTPClient()
    html_page = await utils.retry_func(ft.partial(http_client.make_get_request, url))
    html = bs4.BeautifulSoup(html_page, "html.parser")
    sections = html.find("div", id="searchResults").find_all("section", class_="ticket-item")
    return sections

async def _get_sections_generator(url: str, starting_page: int) -> AsyncGenerator[list[models.CarInfo], None]:
    url = utils.add_size_to_url(url)

    sections_returned = -1
    current_page = starting_page
    while sections_returned != 0:
        url = utils.get_page_url(url, current_page)
        sections = await _get_sections(url)
        sections_returned = len(sections)
        current_page += 1
        if sections_returned == 0:
            logger.info(f"No sections left (page {current_page}) - stopped at {url}")
            break
        yield current_page, sections

async def parse_all_generator(url: str, starting_page: int=0) -> AsyncGenerator[list[models.CarInfo], None]:
    async for page, section in _get_sections_generator(url, starting_page):
        yield page, [utils.get_car_info(s) for s in section]