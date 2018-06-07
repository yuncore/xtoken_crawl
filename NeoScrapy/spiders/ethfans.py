import scrapy
import pymongo
import re
import time
from datetime import datetime
from lxml import html
from NeoScrapy.settings import MONGO_DATABASE
from NeoScrapy.db import CLIENT
from NeoScrapy.db import NeoData


class EthfansItems(scrapy.Item):
    cover = scrapy.Field()
    url = scrapy.Field()
    text = scrapy.Field()
    description = scrapy.Field()
    author_url = scrapy.Field()
    author_name = scrapy.Field()
    time = scrapy.Field()
    read = scrapy.Field()
    pure_text = scrapy.Field()
    html = scrapy.Field()
    likes = scrapy.Field()


class EthafansSpider(scrapy.Spider):
    name = 'ethfans'
    allowed_domains = ['ethfans.org']
    start_urls = ["https://ethfans.org/"]

    def __init__(self, *args, **kwargs):
        super(EthafansSpider, self).__init__(*args, **kwargs)
        self.client = CLIENT
        self.domain = "https://ethfans.org"
        self.db = self.client[MONGO_DATABASE]
        self.cut = False
        # 2015, 1, 1
        self.t = 1420041600

    def parse(self, response):
        self.logger.info('[func] crawl ethfans news [url] {0}'.format(response.url))
        tree = html.fromstring(response.text)
        meta = response.meta
        posts = tree.xpath('//article[@class="post-item"]')
        for post in posts:
            try:
                item = EthfansItems()
                item['cover'] = post.xpath('descendant::img[@class="post-cover"]/@src')[0]
                title = post.xpath('descendant::a[@class="title"]')[0]
                item['url'] = title.attrib['href']
                item['text'] = title.text
                item['description'] = post.xpath('descendant::p[@class="description"]/text()')[0]
                item['author_url'] = post.xpath('descendant::div[@class="meta"]/a/@href')[0]
                item['author_name'] = post.xpath('descendant::div[@class="meta"]/a/text()')[0]
                date_text = post.xpath('descendant::div[@class="meta"]/time/text()')[0]
                item['time'] = self.time_format(date_text)
                if item['time'] < self.t:
                    self.cut = True
                yield scrapy.Request(self.domain + item['url'], callback=self.detail_parse, meta={'item': item})
            except Exception as e:
                self.logger.error(e)
                pass

        if 'page' in meta:
            page = meta['page']
        else:
            page = 1
        if not self.cut:
            yield scrapy.Request(self.domain + '/?page={0}'.format(page + 1), callback=self.parse, meta={'page': page+1})

    def detail_parse(self, response):
        try:
            self.logger.info('[func] crawl article detail news [url] {0}'.format(response.url))
            item = response.meta['item']
            tree = html.fromstring(response.text)
            read_time_text = tree.xpath('//article[@class="post-content"]//p[@class="meta"]/text()[3]')[0]
            item['read'] = self.read_times_format(read_time_text)
            main = tree.xpath('//main[@class="content rhythm"]')[0]
            item['pure_text'] = main.xpath('string(.)').strip()
            item['html'] = html.etree.tostring(main, encoding="utf-8").decode()
            str_like = tree.xpath('//footer[@class="content-footer"]//span[@class="num"]/text()')[0]
            item['likes'] = int(str_like)
            yield item
        except Exception as e:
            self.logger.error(e)
            pass

    @staticmethod
    def read_times_format(text):
        return re.findall(r'\d+', text)[0]

    @staticmethod
    def time_format(str_time):
        d = datetime.strptime(str_time, '%d. %b, %Y')
        return time.mktime(d.timetuple())
