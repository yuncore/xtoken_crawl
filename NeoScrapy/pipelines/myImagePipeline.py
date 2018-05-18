from scrapy.pipelines.images import ImagesPipeline
from NeoScrapy.settings import MONGO_URI, MONGO_PORT, MONGO_DATABASE
from NeoScrapy.db import NeoData
import pymongo
import scrapy


class MyImagesPipeline(ImagesPipeline):
    client = pymongo.MongoClient(MONGO_URI, MONGO_PORT)
    db = client[MONGO_DATABASE]

    def get_media_requests(self, item, info):
        cls = item.__class__.__name__
        if cls == 'CoinMarketItem':
            if 'logo_url' in item:
                yield scrapy.Request(item['logo_url'])
        else:
            return item

    def file_path(self, request, response=None, info=None):
        img_url = request.url
        img_name = img_url[img_url.rfind('/')+1:]
        return 'full/{0}'.format(img_name)
