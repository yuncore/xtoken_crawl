import scrapy
from lxml import html
from NeoScrapy.items import CoinMarketItem


class CoinMarketCapSpider(scrapy.Spider):
    name = 'coinmarketcap'
    allow_domains = ['coinmarketcap.com']
    start_urls = ['https://coinmarketcap.com/all/views/all/']

    def __init__(self, *args, **kwargs):
        super(CoinMarketCapSpider, self).__init__(*args, **kwargs)
        self.domain = 'https://coinmarketcap.com'

    def parse(self, response):
        tree = html.fromstring(response.text)
        for tr in tree.xpath('//*[@id="currencies-all"]//tr')[1:]:
            currency = {}
            tds = tr.findall('td')
            currency['sort'] = int(self.text_format(tds[0].text))
            currency['name'] = self.text_format(tds[1].find('a').text)
            currency['url'] =  self.text_format(tds[1].find('a').attrib['href'])
            currency['symbol'] = self.text_format(tds[2].text)
            yield scrapy.Request(url=self.domain+currency['url'], callback=self.detail_parse, meta=currency)

    def detail_parse(self, response):
        currency = CoinMarketItem()
        meta = response.meta
        try:
            currency['subreddit'] = response.xpath('//script/text()').re(r'[\s|\S]*https://www.reddit.com/r/(.*)\.')[0]
        except IndexError:
            pass
        currency['sort'] = meta['sort']
        currency['name'] = meta['name']
        currency['url'] = meta['url']
        currency['symbol'] = meta['symbol']
        yield currency

    @staticmethod
    def text_format(text):
        if text is None:
            return None
        return text.replace('\n', '').replace('\t', '').strip()
