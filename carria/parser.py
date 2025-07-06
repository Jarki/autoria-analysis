import asyncio
import functools as ft
import logging
import os
from typing import AsyncGenerator

import bs4

from . import client, constants, db_client, models, utils

logger = logging.getLogger(__name__)
    
async def _get_html_page(url: str) -> bs4.BeautifulSoup:
    http_client = client.HTTPClient()
    return await utils.retry_func(ft.partial(http_client.make_get_request, url))

async def _get_sections(url: str) -> list[models.CarInfo]:
    html_page = await _get_html_page(url)
    html = bs4.BeautifulSoup(html_page, "html.parser")
    sections = html.find("div", id="searchResults").find_all("section", class_="ticket-item")
    return sections

async def parse_page(url: str, page: int) -> AsyncGenerator[list[models.CarInfo], None]:
    url = utils.get_page_url(url, page) 
    sections = await _get_sections(url)
    return [utils.get_car_info(s) for s in sections]

async def parse_total_expected(url: str) -> int:
    html_page = await _get_html_page(url)
    html = bs4.BeautifulSoup(html_page, "html.parser")
    return utils.get_total_expected_cars(html)


class Parser:
    def __init__(self):
        self.delay_ms = 540

    def _get_db_client(self, db_name: str) -> db_client.BaseDbClient:
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        client = db_client.DuckDbClient(db_name)
        client.create_database()
        return client

    async def parse_all_from_search(self, url: str, db_name: str="data/search_results.duckdb") -> None:
        logger.info("Starting app")
        total_expected = await parse_total_expected(url)

        db = self._get_db_client(db_name)
        data_df = db.get_all_to_df()
        logger.info(f"Total expected: {total_expected}")
        logger.info(f"Starting with {len(data_df.index)} cars in {db_name}")

        current_page = 0
        url = utils.add_size_to_url(url)
        running_total = 0
        error_count = 0

        while True:
            logger.debug(f"Current page: {current_page}")
            car_infos = await parse_page(url, current_page)

            cars_found = len(car_infos)
            running_total += cars_found
            if cars_found == 0:
                if abs(running_total - total_expected) > running_total * constants.MARGIN_OF_ERROR:
                    logger.warning(f"Found 0 cars, but only have {running_total} out of {total_expected} cars. Retrying...")
                    await asyncio.sleep((self.delay_ms * (error_count + 1)) / 1000)
                    error_count += 1
                    continue
                logger.info(f"No cars left (page {current_page}) - stopped at {url}")
                break

            current_page += 1
            error_count = 0
            db.insert_data(car_infos)
            await asyncio.sleep(self.delay_ms / 1000)

        logger.info(f"Processed {current_page} pages")
        data_df = db.get_all_to_df()
        logger.info(f"Now a total of {len(data_df.index)} cars in {db_name}")