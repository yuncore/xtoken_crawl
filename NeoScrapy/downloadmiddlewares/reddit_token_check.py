import scrapy
import time
import requests
import requests.auth
from NeoScrapy.db import NeoData
from scrapy.exceptions import CloseSpider
from NeoScrapy.settings import REDDIT_SECRET_KEY, REDDIT_CLIENT_ID, REDDIT_USER, REDDIT_PASSWORD


class RedditTokenCheck(object):

    def __init__(self):
        self.spider = None

    def process_request(self, request, spider):
        """
            将访问reddit的token数据存放在mongoDB中，reddit token正常的过期时间为1h
            1.每次发送请求之前从mongoDB中取出token
            2.检查token的locked标志位，如果为True表示系统正在获取新的token
            3.检查token的time标志位，time表示token的获取时间
            4.如果当前时间减去token获取时间大于50分钟，则获取新的token
            5.如果请求发送成功，将返回的token保存在数据库中，并将locked标志位置为false
        """
        if spider.name == 'reddit':
            self.spider = spider
            token = self.spider.db[NeoData.APP_CONFIG].find_one({"name": 'reddit_token'})

            if token is None or token['data'] is None:
                self.get_token()
            elif token['locked']:
                self.spider.logger.info('reddit token locked')
                time.sleep(1)
                scrapy.http.Response(request.url, status=400)
            elif time.time() - token['time'] > 50 * 60:
                time.sleep(1)
                self.get_token()
                scrapy.http.Response(request.url, status=400)
            else:
                request.headers['Authorization'] = 'bearer ' + token['data']

    def get_token(self):
        self.spider.db[NeoData.APP_CONFIG].update_one({"name": 'reddit_token'}, {'$set': {'locked': True}})
        try:
            client_auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_SECRET_KEY)
            post_data = {
                "grant_type": "password",
                "username": REDDIT_USER,
                "password": REDDIT_PASSWORD,
                'duration': 'permanent'
            }
            response = requests.post('https://www.reddit.com/api/v1/access_token',
                                     auth=client_auth, data=post_data)
            res = response.json()
            self.spider.logger.info('access token result {0}'.format(res))
            if 'access_token' in res:
                self.spider.db[NeoData.APP_CONFIG].update_one({"name": 'reddit_token'},
                                                              {'$set': {'data': res['access_token'], 'time': time.time()}},
                                                              upsert=True)
            else:
                self.spider.logger.error('can not get access token {0}'.format(res))
        except Exception as e:
            self.spider.logger.error('access token request error')
            raise CloseSpider('access token error')
        finally:
            self.spider.db[NeoData.APP_CONFIG].update_one({"name": 'reddit_token'}, {'$set': {'locked': False}})



