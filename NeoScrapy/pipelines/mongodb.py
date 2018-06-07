# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from datetime import datetime
from NeoScrapy.db import NeoData, CLIENT


class MongoPipeline(object):
    def __init__(self, mongo_db, relation_db):
        self.MONGO_DATABASE = mongo_db
        self.MONGO_RELATIONBASE = relation_db
        self.client = CLIENT
        self.db = self.client[self.MONGO_DATABASE]
        self.relation_db = self.client[self.MONGO_RELATIONBASE]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            relation_db=crawler.settings.get('MONGO_RELATIONBASE')
        )

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        cls = item.__class__.__name__
        if cls == 'CoinMarketItem':
            self.save_coinmarket(item)
        if cls == 'TokenMarketItem':
            self.save_tokenmarket(item)
        if cls == 'BitCoinTalkLink':
            self.save_btt_link(item)
        if cls == 'BitCoinTalkComment':
            self.save_btt_comment(item)
        if cls == 'BitCoinTalkUserHistory':
            self.save_btt_history(item)
        if cls == 'CoinDeskItem':
            self.save_coindesk_news(item)
        if cls == 'EthfansItems':
            self.save_ethfans_news(item)
        return item

    def save_coinmarket(self, item):
        self.db[NeoData.COINMARKET_CURRENCIES].find_one_and_update({'_id': item['name']},
                                                                   {'$set': {'data': item,
                                                                             'timestamp': datetime.now()}},
                                                                   upsert=True)
        if 'topic_id' in item and len(item['topic_id']) > 0:
            self.relation_db[NeoData.RELATION_CURRENCY_BTT].find_one_and_update({'currency_name': item['name']},
                                                         {'$set': {
                                                             'currency_name': item['name'],
                                                             'topic_id': item['topic_id'][0],
                                                             'ann': True
                                                         }},
                                                         upsert=True)
        if 'github_project' in item and len(item['github_project']) > 0:
            self.relation_db[NeoData.RELAITON_CURRENCY_GITHUB].find_one_and_update({'currency_name': item['name']},
                                                                                   {'$set': {
                                                                                       'currency_name': item['name'],
                                                                                       'full_name': item['github_project'][0]
                                                                                   }},
                                                                                   upsert=True)

    def save_tokenmarket(self, item):
        self.db[NeoData.TOKENMARKET_CURRENCIES].find_one_and_update({'_id': item['name']},
                                                                    {'$set': {'timestamp': datetime.now(),
                                                                              'data': item}},
                                                                    upsert=True)

    def save_btt_link(self, item):
        self.db[NeoData.BTT_LINK].find_one_and_update({'_id': item['id']},
                                                      {'$set': {'timestamp': datetime.now(), 'data': item}},
                                                      upsert=True)

    def save_btt_comment(self, item):
        self.db[NeoData.BTT_COMMENT].find_one_and_update({'_id': item['message_id']},
                                                         {'$set': {'timestamp': datetime.now(), 'data': item}},
                                                         upsert=True)

    def save_btt_history(self, item):
        if item['start']:
            collection_name = NeoData.BTT_USER_HISTORY_START
        else:
            collection_name = NeoData.BTT_USER_HISTORY_POST
        self.db[collection_name].find_one_and_update({'_id': item['msg_id']},
                                                     {'$set': {'timestamp': datetime.now(), 'data': item}},
                                                     upsert=True)

    def save_coindesk_news(self, item):
        self.db[NeoData.COINDESK_NEWS].find_one_and_update({'_id': item['id']}, {'$set': item}, upsert=True)

    def save_ethfans_news(self, item):
        self.db[NeoData.ETHFANS].find_one_and_update({'_id': item['url']}, {'$set': item}, upsert=True)
