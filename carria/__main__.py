import asyncio
import logging
import logging.config

import carria


logging.config.dictConfig(carria.LOGGING_CONFIG)
logger = logging.getLogger("carria")

async def main():
    db_name = "volkswagen.duckdb"
    url = "https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&categories.main.id=1&brand.id[0]=84&damage.not=1"
    starting_page = 0
    delay_ms = 540

    db_client = carria.db_client.DuckDbClient(db_name)
    db_client.create_database()
    data_df = db_client.get_all_to_df()
    logger.info(f"Starting with {len(data_df.index)} cars in {db_name}")

    async for page, car_infos in carria.parser.parse_all_generator(url, starting_page=starting_page):
        logger.debug(f"Found {len(car_infos)} cars on page {page}")
        if page > 0 and page % 5 == 0: 
            logger.info(f"Processed page {page}")
        db_client.insert_data(car_infos)
        await asyncio.sleep(delay_ms / 1000)

    logger.info(f"Processed {page} pages")
    data_df = db_client.get_all_to_df()
    logger.info(f"Now a total of {len(data_df.index)} cars in {db_name}")
    print(data_df.head())


if __name__ == "__main__":
    asyncio.run(main())