import asyncio
import logging
import logging.config

import carria

logging.config.dictConfig(carria.LOGGING_CONFIG)
logger = logging.getLogger("carria")

async def main():
    db_name = "data/hondacivic.duckdb"
    url = "https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&price.currency=1&abroad.not=-1&custom.not=1&damage.not=1&brand.id[0]=28&model.id[0]=265"
    max_concurrent_requests = 5

    parser= carria.parser.Parser(url, db_name, max_concurrent_requests)
    await parser.parse_all_from_search()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopping script")
