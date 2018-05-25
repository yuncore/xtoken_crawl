import scrapy
import re
from lxml import html
from NeoScrapy.items import CoinMarketItem
from NeoScrapy.settings import MONGO_DATABASE
from NeoScrapy.db import NeoData, CLIENT


class CoinMarketCapSpider(scrapy.Spider):
    name = 'coinmarketcap'
    allow_domains = ['coinmarketcap.com']

    def __init__(self, *args, **kwargs):
        super(CoinMarketCapSpider, self).__init__(*args, **kwargs)
        self.client = CLIENT
        self.db = self.client[MONGO_DATABASE]
        self.kwargs = kwargs
        self.PRICE_BASE = 'https://graphs2.coinmarketcap.com/currencies/{0}/'
        self.BASE = 'https://coinmarketcap.com/all/views/all/'
        self.MARKETCAP_ALTCOIN = 'https://graphs2.coinmarketcap.com/global/marketcap-altcoin/'
        self.MARKETCAP_TOTAL = 'https://graphs2.coinmarketcap.com/global/marketcap-total/'
        self.DOMINANCE = 'https://graphs2.coinmarketcap.com/global/dominance/'
        if 'func' in self.kwargs and self.kwargs['func'] in ['DETAIL', 'HISTORY_PRICE', 'TOTAL_MARKET']:
            self.func = kwargs['func']
            self.logger.info('[func] {0} kwargs {1}'.format(self.func, str(self.kwargs)))
        else:
            self.logger.error('no or not allowed func parameter supplied')
        self.with_logo = False
        if 'with_logo' in kwargs and kwargs['with_logo']:
            self.with_logo = True

    def start_requests(self):
        try:
            if self.func == 'DETAIL':
                yield scrapy.Request(self.BASE, callback=self.currency_parse)
            if self.func == 'HISTORY_PRICE':
                currency_id = self.kwargs['currency_id']
                yield scrapy.Request(self.PRICE_BASE.format(currency_id), callback=self.price_parse, meta={'currency_id': currency_id})
            if self.func == 'TOTAL_MARKET':
                yield scrapy.Request(self.MARKETCAP_ALTCOIN, callback=self.total_market_parse,
                                     meta={'type': 'MARKETCAP_ALTCOIN'})
                yield scrapy.Request(self.MARKETCAP_TOTAL, callback=self.total_market_parse,
                                     meta={'type': 'MARKETCAP_TOTAL'})
                yield scrapy.Request(self.DOMINANCE, callback=self.total_market_parse,
                                     meta={'type': 'DOMINANCE'})
        except KeyError:
            self.logger.error('required argument missed')

    def parse(self, response):
        pass

    def currency_parse(self, response):
        tree = html.fromstring(response.text)
        for tr in tree.xpath('//*[@id="currencies-all"]//tr')[1:]:
            currency = {}
            tds = tr.findall('td')
            currency['sort'] = int(self.text_format(tds[0].text))
            currency['url'] = self.text_format(tds[1].find('a').attrib['href'])
            currency['symbol'] = self.text_format(tds[2].text)
            yield scrapy.Request(url='https://coinmarketcap.com'+currency['url'], callback=self.detail_parse, meta=currency)

    def detail_parse(self, response):
        self.logger.info('[func] detail parse [url] {0}'.format(response.url))
        currency = CoinMarketItem()
        meta = response.meta
        currency['sort'] = meta['sort']
        currency['id'] = re.search(r'/(.*)/(.*)/', meta['url']).groups()[1]
        currency['url'] = meta['url']
        currency['symbol'] = meta['symbol']
        currency['website'] = []
        currency['topic_id'] = []
        currency['explorer'] = []
        currency['github_repo'] = []
        currency['github_project'] = []
        currency['message_board'] = []
        currency['chat'] = []
        currency['name'] = response.xpath('//h1[@class="text-large"]/img/@alt').extract()[0]
        links = response.xpath('//ul[@class="list-unstyled"]/li//a')
        for index, link in enumerate(links):
            text = link.xpath('text()').extract()[0]
            href = link.xpath('@href').extract()[0]
            if text.find('Website') > -1:
                currency['website'].append(href)
            if text.find('Announcement') > -1:
                temp = href[href.rfind('=')+1:]
                if temp.find('.') > -1:
                    temp = temp[:temp.rfind('.')]
                currency['topic_id'].append(temp)
            if text.find('Explorer') > -1:
                currency['explorer'].append(href)
            if text.find('Source Code') > -1:
                sub_text = re.search(r'^https://github.com/(.*)', href).groups()[0]
                if str.endswith(sub_text, '/'):
                    sub_text = sub_text[:-1]
                if sub_text.find('/') > -1:
                    currency['github_project'].append(sub_text)
                else:
                    currency['github_repo'].append(sub_text)
            if text.find('Message Board') > -1:
                currency['message_board'].append(href)
            if text.find('Chat') > -1:
                currency['chat'].append(href)
        try:
            currency['subreddit'] = response.xpath('//script/text()').re(r'[\s|\S]*https://www.reddit.com/r/(.*)\.')[0]
        except IndexError:
            pass
        if self.with_logo:
            img = response.xpath('//*[@class="currency-logo-32x32"]/@src').extract()[0]
            if img is not None:
                currency['logo_url'] = img.replace('32x32', '64x64', 1)
        yield currency

    def price_parse(self, response):
        self.logger.info('[func] price parse [url] {0}'.format(response.url))
        currency_id = response.meta['currency_id']
        json_data = response.body_as_unicode()
        if response.status == 200:
            self.db[NeoData.COINMARKET_HISTORY_PRICE].find_one_and_update({'_id': currency_id}, {'$set': {'data': json_data}}, upsert=True)

    def total_market_parse(self, response):
        url_type = response.meta['type']
        self.logger.info('[func] total market parse [url] {0} [type] {1}'.format(response.url, url_type))
        json_data = response.body_as_unicode()
        self.db[NeoData.COINMARKET_TOTAL_MARKET_CAP].find_one_and_update({'type': url_type},
                                                                      {'$set': {
                                                                          'data': json_data
                                                                      }},
                                                                      upsert=True)

    @staticmethod
    def text_format(text):
        if text is None:
            return None
        return text.replace('\n', '').replace('\t', '').strip()
