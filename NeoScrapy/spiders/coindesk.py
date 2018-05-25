import scrapy
import pymongo
import time
from datetime import datetime
from lxml import html
from NeoScrapy.settings import MONGO_DATABASE
from NeoScrapy.db import CLIENT
from NeoScrapy.db import NeoData


class CoinDeskItem(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    author_url = scrapy.Field()
    time_str = scrapy.Field()
    time = scrapy.Field()
    intro = scrapy.Field()
    img = scrapy.Field()


class CoinDeskSpider(scrapy.Spider):
    name = 'coindesk'
    allowed_domains = ['coindesk.com']
    start_urls = ['http://www.coindesk.com']

    def __init__(self, *args, **kwargs):
        super(CoinDeskSpider, self).__init__(*args, **kwargs)
        self.client = CLIENT
        self.db = self.client[MONGO_DATABASE]
        self.end_time = self.calc_latest_record()
        self.continue_flag = True

    def parse(self, response):
        self.logger.info('[func] crawl coindesk news [url] {0}'.format(response.url))
        tree = html.fromstring(response.text)
        meta = response.meta
        articles = tree.xpath('//*[@class="article medium bordered"]')
        for index, article in enumerate(articles):
            try:
                item = CoinDeskItem()
                item['id'] = article.attrib['id']
                title_dom = article.xpath('descendant::div[@class="post-info"]/h3/a')[0]
                item['url'] = title_dom.attrib['href']
                item['title'] = title_dom.text
                time_str = article.xpath('descendant::p[@class="timeauthor"]/time/@datetime')[0]
                item['time_str'] = time_str
                item['time'] = self.time_format(time_str)
                author_dom = article.xpath('descendant::p[@class="timeauthor"]/cite/a')[0]
                item['author'] = author_dom.text
                item['author_url'] = author_dom.attrib['href']
                item['intro'] = article.xpath('descendant::p')[1].text
                item['img'] = article.xpath('descendant::div[@class="picture"]//img/@data-lazy-src')[0]
                if item['time'] < self.end_time:
                    self.continue_flag = False
                yield item
            except Exception:
                pass

        # 统计现在是第几页
        if 'page' in meta:
            page = meta['page']
        else:
            page = 1
        if self.continue_flag:
            url = 'https://www.coindesk.com/page/{0}/'.format(page+1)
            yield scrapy.Request(url, callback=self.parse, meta={'page': page+1})

    def calc_latest_record(self):
        cs = self.db[NeoData.COINDESK_NEWS].find({}).sort([('time', pymongo.DESCENDING)]).limit(1)
        return cs[1]['time']

    @staticmethod
    def time_format(str_time):
        d = datetime.strptime(str_time[:-6], '%Y-%m-%dT%H:%M:%S')
        return time.mktime(d.timetuple())

    @staticmethod
    def text_format(text):
        if text == 'N/A':
            return None
        if text is None:
            return None
        return text.replace('\n', '').replace('\t', '').strip()


if __name__ == '__main__':
    cs = CoinDeskSpider()
    print(cs.calc_latest_record())