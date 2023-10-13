import time
from urllib.parse import urljoin
import csv
from bs4 import BeautifulSoup
import httpx
import pandas as pd

from dataclasses import dataclass

BASE_URL = "https://jam.ua/"
PEDALS_URL = urljoin(BASE_URL, "ua/effect_pedals")


@dataclass
class Pedal:
    title: str
    price: float
    rating: int
    presence_in_store: bool
    num_of_reviews: int


async def get_pedal_price(product_soup):
    if product_soup.select_one(".product__price-expected"):
        return 0
    if product_soup.select_one(".product__price-action"):
        return float(product_soup.select_one(".new").text.removesuffix(" грн").replace(" ", ""))
    else:
        return float(product_soup.select_one(".product__price").text.removesuffix(" грн").replace(" ", ""))


async def get_pedal_rating(product_soup):
    rating = int(product_soup.select_one(".rating-stars-i")["style"].split()[1].split("%")[0])
    return int(rating / 25)


async def get_pedal_presence(product_soup):
    if product_soup.select_one(".presence-in-store"):
        return True
    if product_soup.select_one(".product-presence.presence-not-in-store"):
        return False
    else:
        return False


async def get_num_of_reviews(product_soup):
    if product_soup.select_one(".product-reviews"):
        return int(product_soup.select_one(".product-reviews").text)
    else:
        return 0


async def parse_single_pedal(product_soup: BeautifulSoup) -> Pedal:
    return Pedal(
        title=product_soup.select_one(".product__title").text,
        price=await get_pedal_price(product_soup),
        rating=await get_pedal_rating(product_soup),
        presence_in_store=await get_pedal_presence(product_soup),
        num_of_reviews=await get_num_of_reviews(product_soup),
    )


async def parse_single_pedal_page(page_soup: BeautifulSoup) -> [Pedal]:
    products = page_soup.select(".product-card")
    return [await parse_single_pedal(product_soup) for product_soup in products]


async def get_num_of_pages(soup: BeautifulSoup) -> int:
    pagination = soup.select_one(".paginate__block")
    if pagination is None:
        return 1
    return int(pagination.select("li")[-2].text)


async def parse_all_pedals() -> [Pedal]:
    async with httpx.AsyncClient() as client:
        page = await client.get(PEDALS_URL)
    first_page_soup = BeautifulSoup(page.text, "html.parser")

    num_pages = get_num_of_pages(first_page_soup)

    all_pedals = await parse_single_pedal_page(first_page_soup)

    for num_page in range(2, num_pages + 1):
        async with httpx.AsyncClient() as client:
            page = await client.get(PEDALS_URL, params={"list": num_page})
        soup = BeautifulSoup(page.text, "html.parser")
        all_pedals.extend(await parse_single_pedal_page(soup))

    return all_pedals


def add_new_data_to_list_of_products(data: [Pedal]) -> None:
    existing_data = pd.read_csv("pedals.csv")
    new_data = pd.DataFrame(data)
    combined_data = pd.concat([existing_data, new_data], ignore_index=True)
    combined_data.to_csv("pedals.csv", index=False)


def write_data_into_csv_file(data):
    df = pd.DataFrame(data)
    df.to_csv("pedals.csv", index=False)


async def main():
    start = time.time()
    all_pedals = await parse_all_pedals()
    write_data_into_csv_file(all_pedals)
    finish = time.time()
    print(f"Program executes in {finish - start} seconds")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
