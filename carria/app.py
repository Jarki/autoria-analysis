import asyncio
import logging
import os

from . import constants, db_client, parser, utils

logger = logging.getLogger(__name__)

class App:
    def __init__(self):
        self.delay_ms = 540

    def _get_db_client(self, db_name: str) -> db_client.BaseDbClient:
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        client = db_client.DuckDbClient(db_name)
        client.create_database()
        return client

    async def parse_all_from_search(self, url: str, db_name: str="data/search_results.duckdb") -> None:
        logger.info("Starting app")
        total_expected = await parser.parse_total_expected(url)

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
            car_infos = await parser.parse_page(url, current_page)

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