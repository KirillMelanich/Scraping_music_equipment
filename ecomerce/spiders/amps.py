import scrapy


class AmpsSpider(scrapy.Spider):
    name = "amps"
    allowed_domains = ["jam.ua"]
    start_urls = ["https://jam.ua/ua/guitar_combo"]

    def parse(self, response):
        pass
