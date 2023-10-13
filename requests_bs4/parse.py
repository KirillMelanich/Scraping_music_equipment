import logging
import os
import sys
import time

from bs4 import BeautifulSoup
import requests
import pandas as pd
from dataclasses import dataclass

from urllib .parse import urljoin


BASE_URL = "https://jam.ua/"
AMP_URL = urljoin(BASE_URL, "ua/guitar_combo")

logging.basicConfig(
     level=logging.DEBUG,
     format= '[%(levelname)8s]: %(message)s',
     handlers=[
         logging.FileHandler("parser.log"),
         logging.StreamHandler(sys.stdout)
     ]
 )


@dataclass
class Product:
    title: str
    presence_in_store: bool
    rating: int
    num_of_reviews: int
    price: float


def get_price(product_soup: BeautifulSoup) -> float:
    if product_soup.select_one(".product__price.none"):
        return 0
    if product_soup.select_one(".product__price"):
        return float(product_soup.select_one(".product__price").text.removesuffix(" грн").replace(" ", ""))
    elif product_soup.select_one(".product__price-action"):
        return float(product_soup.select_one(".new").text.removesuffix(" грн").replace(" ", ""))


def get_presence_in_store(product_soup: BeautifulSoup) -> bool:
    if product_soup.select_one(".presence-in-store") is None:
        return False
    if product_soup.select_one(".presence-in-store").text == "В наявності":
        return True
    return False


def get_rating(product_soup: BeautifulSoup) -> int:
    num = product_soup.select_one(".rating-stars-i")["style"].split()[1].split("%")[0]
    return int(int(num) / 25)


def get_num_reviews(product_soup: BeautifulSoup) -> int:
    if product_soup.select_one(".product-reviews"):
        return int(product_soup.select_one(".product-reviews").text)
    else:
        return 0


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".product__title").text,
        price=get_price(product_soup),
        presence_in_store=get_presence_in_store(product_soup),
        rating=get_rating(product_soup),
        num_of_reviews=get_num_reviews(product_soup),
    )


def get_num_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select_one(".paginate__block")

    if pagination is None:
        return 1

    return int(pagination.select("li")[-2].text)


def get_single_page_amps(page_soup: BeautifulSoup) -> [Product]:

    products = page_soup.select(".product-card")

    return [parse_single_product(product_soup) for product_soup in products]


def get_amps_products() -> [Product]:
    logging.info(f"Nachnem persit kombari")
    logging.info(f"Dolboeb smotrit kak parsitsya stranica #1")
    page = requests.get(AMP_URL).content
    first_page_soup = BeautifulSoup(page, "html.parser")

    num_pages = get_num_pages(first_page_soup)

    all_amps = get_single_page_amps(first_page_soup)

    for page_num in range(2, num_pages + 1):
        logging.info(f"Dolboeb smotrit kak parsitsya stranica #{page_num}")
        page = requests.get(AMP_URL, params={"list": page_num}).content
        soup = BeautifulSoup(page, "html.parser")
        all_amps.extend(get_single_page_amps(soup))

    return all_amps


def wright_data_into_csv_file(data):
    df = pd.DataFrame(data)
    df.to_csv("amplifiers.csv", index=False)


def main():
    start = time.time()
    wright_data_into_csv_file(get_amps_products())
    finish = time.time()
    print(f"Your program executes in {finish - start} seconds")


if __name__ == '__main__':
    main()