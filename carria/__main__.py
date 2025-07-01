import asyncio
import logging
import logging.config

import carria


logging.config.dictConfig(carria.LOGGING_CONFIG)
logger = logging.getLogger("carria")

async def main():
    db_name = "all_cars.duckdb"
    url = "https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&categories.main.id=1&price.currency=1&abroad.not=0&custom.not=-1&damage.not=1"
    starting_page = 0
    delay_ms = 540

    db_client = carria.db_client.DuckDbClient(db_name)
    db_client.create_database()
    data_df = db_client.get_all_to_df()

    total_expected = await carria.parser.parse_total_expected(url)
    total_expected -= starting_page * carria.constants.PAGE_SIZE
    logger.info(f"Total expected: {total_expected}")
    logger.info(f"Starting with {len(data_df.index)} cars in {db_name}")

    current_page = starting_page
    url = carria.utils.add_size_to_url(url)
    running_total = 0
    error_count = 0
    while True:
        logger.debug(f"Current page: {current_page}")
        car_infos = await carria.parser.parse_page(url, current_page)

        cars_found = len(car_infos)
        running_total += cars_found
        if cars_found == 0:
            if abs(running_total - total_expected) > running_total * carria.constants.MARGIN_OF_ERROR:
                logger.warning(f"Found 0 cars, but only have {running_total} out of {total_expected} cars. Retrying...")
                await asyncio.sleep((delay_ms * (error_count + 1)) / 1000)
                error_count += 1
                continue
            logger.info(f"No cars left (page {current_page}) - stopped at {url}")
            break

        current_page += 1
        error_count = 0
        db_client.insert_data(car_infos)
        await asyncio.sleep(delay_ms / 1000)

    logger.info(f"Processed {current_page} pages")
    data_df = db_client.get_all_to_df()
    logger.info(f"Now a total of {len(data_df.index)} cars in {db_name}")
    print(data_df.head())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopping script")
