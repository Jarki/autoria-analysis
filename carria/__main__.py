import asyncio
import logging

import carria


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    db_client = carria.db_client.DuckDbClient("golf_gti.duckdb")
    db_client.create_database()

    url = "https://auto.ria.com/uk/search/?categories.main.id=1&brand.id[0]=84&model.id[0]=2813&indexName=auto,order_auto,newauto_search&limit=100&page=0&size=100"
    car_infos = await carria.parser.parse_all(url)

    logger.info(f"Found {len(car_infos)} cars")
    db_client.insert_data(car_infos)
    data_df = db_client.get_all_to_df()
    print(data_df.head())


if __name__ == "__main__":
    asyncio.run(main())