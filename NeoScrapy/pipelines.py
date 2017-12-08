# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from datetime import datetime


class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db, mongo_port):
        self.mongo_port = mongo_port
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_port=crawler.settings.get('MONGO_PORT'),
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri, self.mongo_port)
        self.db = self.client[self.mongo_db]

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
        return item

    def save_coinmarket(self, item):
        collection_name = 'coinmarket_currency_list'
        self.db[collection_name].find_one_and_update({'_id': item['name']},
                                                     {'$set': {'timestamp': datetime.now(), 'data': item}},
                                                     upsert=True)

    def save_tokenmarket(self, item):
        collection_name = 'tokenmarket_currency_list'
        self.db[collection_name].find_one_and_update({'_id': item['name']},
                                                     {'$set': {'timestamp': datetime.now(), 'data': item}},
                                                     upsert=True)

    def save_btt_link(self, item):
        collection_name = 'btt_link'
        self.db[collection_name].find_one_and_update({'_id': item['id']},
                                                     {'$set': {'timestamp': datetime.now(), 'data': item}},
                                                     upsert=True)

    def save_btt_comment(self, item):
        collection_name = 'btt_comment'
        self.db[collection_name].find_one_and_update({'_id': item['message_id']},
                                                     {'$set': {'timestamp': datetime.now(), 'data': item}},
                                                     upsert=True)

    def save_btt_history(self, item):
        if item['start']:
            collection_name = 'btt_history_start'
        else:
            collection_name = 'btt_history_post'
        self.db[collection_name].find_one_and_update({'_id': item['msg_id']},
                                                     {'$set': {'timestamp': datetime.now(), 'data': item}},
                                                     upsert=True)
