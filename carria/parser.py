import asyncio
import logging
import os

import bs4

from . import client, constants, db_client, models, utils

logger = logging.getLogger(__name__)


class Parser:
    ERROR_RETRIES = 3

    def __init__(self, url: str, db_name: str="data/search_results.duckdb", max_concurrent_requests: int=5) -> None:
        self.http_client = client.HTTPClient()
        self.url = utils.add_size_to_url(url)
        self.db_client = self._get_db_client(db_name)

        self._expected_offers = 0
        self._processed_offers = 0
        self._expected_pages = 0
        self._processed_pages = 0

        self.default_moe = 0.01

        self.write_lock = asyncio.Lock()

        self.errored_queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def _set_processed_pages(self, value: int) -> None:
        async with self.write_lock:
            self._processed_pages = value

    async def _set_processed_offers(self, value: int) -> None:
        async with self.write_lock:
            self._processed_offers = value

    def _get_db_client(self, db_name: str) -> db_client.BaseDbClient:
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        client = db_client.DuckDbClient(db_name)
        client.create_database()
        return client
    
    async def _insert_data(self, data: list[models.CarInfo]) -> None:
        async with self.write_lock:
            self.db_client.insert_data(data)

    async def _get_cars_from_url(self, url: str, expected_cars: int, margin_of_error: float = 0.0) -> list[models.CarInfo]: 
        html_page = await self.http_client.make_get_request(url)
        html = bs4.BeautifulSoup(html_page, "html.parser")
        sections = html.find("div", id="searchResults").find_all("section", class_="ticket-item")
        if abs(expected_cars - len(sections)) > expected_cars * margin_of_error:
            raise Exception(f"Expected {expected_cars} cars, but got {len(sections)}")
        return [utils.get_car_info(s) for s in sections]
    
    async def _get_total_expected(self) -> int:
        html_page = await self.http_client.make_get_request(self.url)
        html = bs4.BeautifulSoup(html_page, "html.parser")
        return utils.get_total_expected_cars(html)
    
    async def _process_page(self, page: int) -> None:
        async with self._semaphore:
            logger.debug(f"Processing page {page}")
            expected_cars = min(constants.PAGE_SIZE, self._expected_offers - constants.PAGE_SIZE * page)
            moe = self.default_moe
            if expected_cars < constants.PAGE_SIZE: # case for last page
                moe = 0.5
            try:
                car_info_list = await self._get_cars_from_url(utils.get_page_url(self.url, page), expected_cars, moe)
                if len(car_info_list) > 0:
                    # this is not async so slows down but it's ok
                    await self._insert_data(car_info_list)
                    await self._set_processed_pages(self._processed_pages + 1)
                    await self._set_processed_offers(self._processed_offers + len(car_info_list))
            except Exception as e:
                logger.error(f"Error while parsing page {page}: {e}")
                self.errored_queue.put_nowait(page)

    async def parse_all_from_search(self) -> None:
        logger.info("Starting parser. Retrieving total expected offers...")
        self._expected_offers = await self._get_total_expected()
        self._expected_pages = self._expected_offers // constants.PAGE_SIZE + 1
        logger.info(f"Expecting {self._expected_offers} cars on {self._expected_pages} pages")

        tasks = [self._process_page(i) for i in range(self._expected_pages)]
        await asyncio.gather(*tasks)
        logger.info(f"Successfully processed {self._processed_offers} offers on {self._processed_pages} pages")

        if not self.errored_queue.empty():
            for i in range(self.ERROR_RETRIES):
                self.default_moe *= 2
                logger.info(f"Retrying errored pages ({i + 1} of {self.ERROR_RETRIES})")

                tasks  = []
                while not self.errored_queue.empty():
                    tasks.append(self._process_page(self.errored_queue.get_nowait()))

                await asyncio.gather(*tasks)

        logger.info(f"Successfully processed {self._processed_offers} offers on {self._processed_pages} pages")
        logger.info(f"Parser is done. Total errors left unprocessed: {self.errored_queue.qsize()}" +\
                    ("(" + ", ".join(map(str, self.errored_queue.queue)) + ")" if self.errored_queue.qsize() > 0 else ""))