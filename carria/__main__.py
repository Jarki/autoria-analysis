import asyncio
import logging
import logging.config

import carria

logging.config.dictConfig(carria.LOGGING_CONFIG)
logger = logging.getLogger("carria")

async def main():
    db_name = "data/search_results.duckdb"
    url = "https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&categories.main.id=1&price.currency=1&abroad.not=0&custom.not=-1&damage.not=1"

    parser= carria.parser.Parser()
    await parser.parse_all_from_search(url, db_name)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopping script")
