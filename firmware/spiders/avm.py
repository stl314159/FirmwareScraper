from re import search
from typing import Union

from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class AvmSpider(Spider):
    name = 'avm'

    device_classes = {'fritzbox': 'Home Router', 'fritzwlan': ['Repeater', 'Wifi Stick'], 'fritzpowerline': 'PLC Adapter'}

    start_urls = [
        'http://download.avm.de/fritzbox/',
        'http://download.avm.de/fritzwlan/',
        'http://download.avm.de/fritzpowerline/'
    ]

    def parse(self, response: Response) -> Request:
        for product_url in self.link_extractor(response=response, prefix=('beta', 'tools', 'license', '..')):
            yield Request(url=product_url, callback=self.parse_product)

    def parse_product(self, response: Response) -> Union[FirmwareItem, Request]:
        path = response.request.url.split('/')[:-1]
        if path[-1] == 'fritz.os':
            yield from self.prepare_item_download(response=response, path=path)
        else:
            for sub in self.link_extractor(response=response, prefix=('recover', '..')):
                yield Request(url=response.urljoin(sub), callback=self.parse_product)

    def prepare_item_download(self, response: Response, path: str) -> FirmwareItem:
        release_dates = self.date_extractor(response)
        for index, file_url in enumerate(self.link_extractor(response=response, prefix='..')):
            if file_url.endswith('.image'):
                loader = ItemLoader(item=FirmwareItem(), selector=file_url)
                loader.add_value('file_urls', file_url)
                loader.add_value('vendor', 'avm')
                loader.add_value('device_name', path[-3])
                loader.add_value('device_class', path[-4])
                loader.add_value('release_date', release_dates[index])
                yield loader.load_item()

    @staticmethod
    def link_extractor(response: Response, prefix: Union[str, tuple]) -> list:
        return [response.urljoin(p) for p in response.xpath('//a/@href').extract() if not p.startswith(prefix)]

    @staticmethod
    def date_extractor(response: Response) -> list:
        release_dates = list()
        for text in response.xpath('//pre/text()').extract():
            match = search(r'(\d{2}-\w{3}-\d{4} \d{2}:\d{2})', text)
            if match:
                release_dates.append(match.group(1))

        return release_dates
