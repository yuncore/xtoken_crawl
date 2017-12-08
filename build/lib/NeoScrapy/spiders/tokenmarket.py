import scrapy
from lxml import html
import pymongo
from NeoScrapy.items import TokenMarketItem


class TokenMarketSpider(scrapy.Spider):
    name = 'tokenmarket'
    allow_domains = ['tokenmarket.net']

    def __init__(self):
        super(TokenMarketSpider, self).__init__()
        self.start_urls = ['https://tokenmarket.net/blockchain/all-assets?batch_num=0&batch_size=100']
        self.count = 0

    def parse(self, response):
        tree = html.fromstring(response.text)
        for tr in tree.xpath('//*[@id="table-all-assets-wrapper"]//tr')[1:]:
            currency = {}
            tds = tr.findall('td')
            try:
                currency['logo'] = tds[0].find('a').attrib['href']
                currency['name'] = self.text_format(tds[2].find('div/a').text)
                currency['local_url'] = tds[2].find('div/a').attrib['href']
                currency['symbol'] = self.text_format(tds[3].text)
                currency['description'] = self.text_format(tds[4].text)
            except AttributeError as e:
                self.logger.error('parse tokenmarket currency list page error :: {0} {1}'.format(str(currency), str(e)))
            else:
                yield scrapy.Request(currency['local_url'], callback=self.detail_parse, meta=currency)
        url = tree.xpath('//*[@id="table-all-assets-wrapper"]/div/ul/li[3]/a')[0].attrib['href']
        if url != 'javascript:void(0)':
            yield scrapy.Request(url, callback=self.parse)

    def detail_parse(self, response):
        tree = html.fromstring(response.text)
        currency = TokenMarketItem()
        currency['logo'] = response.meta['logo']
        currency['name'] = response.meta['name']
        currency['local_url'] = response.meta['local_url']
        currency['symbol'] = response.meta['symbol']
        currency['description'] = response.meta['description']
        currency['follow'] = response.css('.btn-follow-bottom::text').re(r'\d+')[0]
        try:
            for tr in tree.xpath('//*[@class="table table-asset-data"]//tr'):
                text = str(tr.text_content()).replace("  ", "")
                if text.find('not available') > -1:
                    continue
                if text.find('Website') > -1:
                    currency['website'] = tr.find('td/a').attrib['href']
                    continue
                if text.find('Blog') > -1:
                    currency['blog'] = tr.find('td/a').attrib['href']
                    continue
                if text.find('Whitepaper') > -1:
                    currency['white_paper'] = tr.find('td/a').attrib['href']
                    continue
                if text.find('Facebook') > -1:
                    currency['facebook'] = tr.find('td/a').attrib['href']
                    continue
                if text.find('Twitter') > -1:
                    currency['twitter'] = tr.find('td/a').attrib['href']
                    continue
                if text.find('Linkedin') > -1:
                    currency['linkedin'] = tr.find('td/a').attrib['href']
                    continue
                if text.find('Slack') > -1:
                    currency['slack'] = tr.find('td/a').attrib['href']
                    continue
                if text.find('Telegram') > -1:
                    currency['telegram'] = tr.find('td/a').attrib['href']
                    continue
                if text.find('Github') > -1:
                    currency['github'] = tr.find('td/a').attrib['href']
                    continue
        except AttributeError as e:
            self.logger.error('parse tokenmarket currency detail error :: {0} {1}'.format(str(currency), str(e)))
        yield currency

    @staticmethod
    def text_format(text):
        if text is None:
            return None
        return text.replace('\n', '').replace('\t', '').strip()