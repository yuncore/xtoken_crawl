import scrapy
import pymongo
import time
import re
from lxml import html
from NeoScrapy.settings import MONGO_URI, MONGO_PORT, MONGO_DATABASE
from NeoScrapy.db import NeoData


class IcoHolderSpider(scrapy.Spider):
    name = 'icoholder'
    allow_domain = 'icoholder.com'
    prefile = 'https://icoholder.com'
    start_urls = ['https://icoholder.com/en/icos/past?sort=r.general&direction=desc&page=0']
    client = pymongo.MongoClient(MONGO_URI, MONGO_PORT)
    db = client[MONGO_DATABASE]

    def parse(self, response):
        self.logger.info('[func] parse [url] {0}'.format(response.url))
        tree = html.fromstring(response.text)
        rows = tree.xpath('//*[@class="ico-list-row "]')
        for r in rows:
            name = r.xpath('descendant::*[@class="ico-list-name-d"]/a/text()')[0]
            try:
                ico_date_from_text = r.xpath('descendant::*[@class="ico-list-date-from"]/text()')[0]
                ico_date_from = self.get_time_format(ico_date_from_text)
            except Exception:
                ico_date_from = None
            try:
                ico_date_to_text = r.xpath('descendant::*[@class="ico-list-date-to"]/text()')[0]
                ico_date_to = self.get_time_format(ico_date_to_text)
            except Exception:
                ico_date_to = None
            try:
                ico_raised_text = r.xpath('descendant::*[@class="ico-list-raised"]/text()')[0]
                ico_raised = self.text_format(ico_raised_text)
            except Exception:
                ico_raised = None
            self.db[NeoData.ICOHOLDER_BASE].find_one_and_update(
                {'name': name},
                {'$set': {
                    'name': name,
                    'ico_date_from': ico_date_from,
                    'ico_date_to': ico_date_to,
                    'ico_raised': ico_raised
                }},
                upsert=True
            )
        try:
            next_url = self.prefile + tree.xpath('//*[@class="pagination pagination-new"]//li/a[@rel="next"]/@href')[0]
            yield scrapy.Request(next_url, callback=self.parse)
        except Exception:
            self.logger.info('end of list')
            pass

    @staticmethod
    def get_time_format(text):
        if text is None:
            return None
        try:
            return time.mktime(time.strptime(text, '%b %d, %Y'))
        except Exception:
            return None

    @staticmethod
    def text_format(text):
        try:
            return int(re.sub(r'\D', '', text))
        except Exception:
            return None


if __name__ == '__main__':
    client = pymongo.MongoClient(MONGO_URI, MONGO_PORT)
    db = client[MONGO_DATABASE]
    cs = db[NeoData.ICOHOLDER_BASE].find()
    for i in cs:
        db[NeoData.ICOHOLDER_BASE].find_one_and_update({"_id": i['_id']}, {'$set': {'ico_raised': IcoHolderSpider.text_format(i['ico_raised'])}})