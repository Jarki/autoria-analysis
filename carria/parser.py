import logging

import bs4

from . import utils
from . import models
from . import client

logger = logging.getLogger(__name__)

async def _get_all_sections(url: str, http_client: client.HTTPClient) -> list[bs4.element.Tag]:
    all_sections = []
    current_page = 0
    while current_page < 100:
        logger.debug(f"Current page: {current_page}")
        url = utils.get_page_url(url, current_page)
        result = await http_client.make_get_request(url)
        html = bs4.BeautifulSoup(result, "html.parser")
        sections = html.find("div", id="searchResults").find_all("section", class_="ticket-item")
        if len(sections) == 0:
            logger.debug("No sections left")
            break
            
        current_page += 1
        all_sections.extend(sections)
    return all_sections

async def parse_all(url) -> list[models.CarInfo]:
    http_client = client.HTTPClient()
    sections = await _get_all_sections(url, http_client)
    return [utils.get_car_info(s) for s in sections]