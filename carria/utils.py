import asyncio
import functools
import functools as ft
import logging
import re
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import bs4

from . import models, utils

logger = logging.getLogger(__name__)

def parse_integer(value: str) -> int:
    value = value or -1
    try:
        return int(value)
    except ValueError:
        return -1

def get_page_url(url: str, page_num: int):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params['page'] = page_num
    new_query = urlencode(params, doseq=True)
    new_url = urlunparse(parsed._replace(query=new_query))
    return new_url

def add_size_to_url(url: str, size: int=100) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params['size'] = size
    new_query = urlencode(params, doseq=True)
    new_url = urlunparse(parsed._replace(query=new_query))
    return new_url

def __try_get_text(tag: bs4.element.Tag, default: str = "") -> str:
    if tag is not None:
        return tag.get_text(strip=True)
    return default

def __try_find(func: Callable) -> Callable: 
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Error while parsing: {e} ({func.__name__})")
            return ""
    return wrapper

@__try_find
def get_price_and_currency(section: bs4.element.Tag) -> tuple[int, str]:
    price_item = section.find("div", class_="price-ticket")
    if price_item is not None:
        price = int(price_item.get_attribute_list("data-main-price")[0])
        curr = price_item.get_attribute_list("data-main-currency")[0]
        return price, curr
    return -1, ""

@__try_find
def get_mileage(section: bs4.element.Tag) -> str:
    return __try_get_text(section.find("li", class_="js-race")).split(" ")[0]

@__try_find
def get_location(section: bs4.element.Tag) -> str:
    location: str = __try_get_text(section.find("li", class_="js-location"))
    return location.strip()

@__try_find
def get_engine(section: bs4.element.Tag) -> str:
    return section.find("div", class_="hide").get("data-modification-name")

@__try_find
def get_transmission(section: bs4.element.Tag) -> str:
    return __try_get_text(section.find_all("li", class_="item-char")[3])

@__try_find
def get_vin(section: bs4.element.Tag) -> str:
    return __try_get_text(section.find("span", class_="label-vin").find("span"))

@__try_find
def get_state_num(section: bs4.element.Tag) -> str:
    return __try_get_text(section.find("span", class_="state-num").find(string=True, recursive=False))

@__try_find
def get_year(section: bs4.element.Tag) -> str:
    return __try_get_text(section.find("a", class_="address").find_all(string=True, recursive=False)[1])

@__try_find
def get_generation(section: bs4.element.Tag) -> str:
    return section.find("div", class_="hide").get("data-generation-name")

@__try_find
def get_link(section: bs4.element.Tag) -> str:
    return section.find("a", class_="m-link-ticket").get("href")

@__try_find
def get_make(section: bs4.element.Tag) -> models.CarInfo:
    return section.find("div", class_="hide").get("data-mark-name")

@__try_find
def get_model(section: bs4.element.Tag) -> models.CarInfo:
    return section.find("div", class_="hide").get("data-model-name")

@__try_find
def get_autoria_id(section: bs4.element.Tag) -> str:
    return section.find("div", class_="hide").get("data-id")

def get_car_info(section: bs4.element.Tag) -> models.CarInfo:
    with open("car.html", "w") as f:
        f.write(section.prettify())
    price, curr = get_price_and_currency(section)
    id_ = get_autoria_id(section)
    mileage = get_mileage(section)
    location = get_location(section)
    engine = get_engine(section)
    transmission = get_transmission(section)
    vin = get_vin(section) or None
    state_num = get_state_num(section)
    make = get_make(section) 
    model = get_model(section)
    year = get_year(section)
    generation = get_generation(section)
    link = get_link(section)

    year = utils.parse_integer(year)
    price = utils.parse_integer(price)
    mileage = utils.parse_integer(mileage)
    
    return models.CarInfo(
        id=id_,
        make=make,
        model=model,
        year=year, 
        generation=generation,
        price=price,
        mileage=mileage,
        location=location,
        engine=engine,
        transmission=transmission,
        vin=vin,
        plate=state_num,
        link=link,
        currency=curr,
    )

def get_total_expected_cars(html_page: bs4.BeautifulSoup) -> int:
    try:
        with open("car.html", "w") as f:
            f.write(str(html_page.prettify()))
        # TODO: is this the best way?
        count = re.search(r"window.ria.server.resultsCount\s*=\s*Number\((\d+)\);", str(html_page)).group(1)
        return int(count)
    except Exception:
        return 0

async def retry_func(func: ft.partial, retries: int=3, delay: int=1000) -> Any:
    for i in range(retries):
        try:
            return await func()
        except Exception as e:
            logger.error(f"Error while parsing: {e}, {func.func.__name__}")
            logger.debug(f"Retry {i + 1}. Retrying in {delay} ms")
            await asyncio.sleep((delay + (i ** 2) * delay) / 1000)
    raise Exception(f"Failed to parse after {retries} retries")