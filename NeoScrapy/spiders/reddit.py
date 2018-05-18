from NeoScrapy.settings import MONGO_URI, MONGO_PORT, MONGO_DATABASE
from NeoScrapy.db import NeoData
import time
import pymongo
import scrapy
import json


class RedditSpider(scrapy.Spider):
    name = 'reddit'
    allowed_domains = ['reddit.com']

    def __init__(self, *args, **kwargs):
        """
        func:
            LINK: 获取帖子的信息，所需参数： srname [subreddit名称]
            COMMENT: 获取评论信息，默认获取给定subreddit下面最近一个月内发帖的评论 ， 所需参数：srname [subreddit名称]
            USER: 获取单个用户的基本信息 ，所需参数： username [用户的昵称]
            SUBREDDIT: 获取话题的基本信息，所需参数: srname [subreddit 的名字]
            HISTORY: 获取用户的历史，所需参数: username [用户的昵称]
        force: 当func == comment的时候，force为true表示获取数据库中所有帖子的评论
        """
        super(RedditSpider, self).__init__(*args, **kwargs)
        self.client = pymongo.MongoClient(MONGO_URI, MONGO_PORT)
        self.db = self.client[MONGO_DATABASE]
        self.LINK_BASE = ['https://oauth.reddit.com/r/{0}/new?limit=100',
                          'https://oauth.reddit.com/r/{0}/hot?limit=100&sort=top&t=all',
                          'https://oauth.reddit.com/r/{0}/top?limit=100']
        self.COMMENT_BASE = 'https://oauth.reddit.com/comments/article?article={0}&limit={1}&depth={2}&showmore={3}'
        self.USER_BASE = 'https://oauth.reddit.com/user/{0}/about'
        self.SUBREDDIT_BASE = 'https://oauth.reddit.com/r/{0}/about'
        self.USER_HISTORY_BASE = ['https://oauth.reddit.com/user/{0}/comments?limit=100&t=all',
                                  'https://oauth.reddit.com/user/{0}/submitted?limit=100&t=all']
        self.kwargs = kwargs
        self.logger.info(self.kwargs)
        if 'func' in self.kwargs and self.kwargs['func'] in ['LINK', 'COMMENT', 'USER', 'SUBREDDIT', 'HISTORY']:
            self.func = kwargs['func']
            self.logger.info('[func] {0} kwargs {1}'.format(self.func, str(self.kwargs)))
        else:
            self.logger.error('no or not allowed func parameter supplied')
        self.force = False
        if 'force' in kwargs and kwargs['force'] == 'True':
            self.force = True

    def start_requests(self):
        try:
            if self.func == 'LINK':
                sr_name = self.kwargs['srname']
                for url in self.LINK_BASE:
                    yield scrapy.Request(url.format(sr_name), callback=self.link_parse,
                                         meta={'base': url, 'srname': sr_name})
            if self.func == 'COMMENT':
                sr_name = self.kwargs['srname']
                if self.force:
                    # 强制获取数据库中所有帖子下面的评论
                    articles = self.db[NeoData.REDDIT_LINK].find({'data.subreddit': sr_name})
                else:
                    # 默认获取最近一个月的帖子
                    articles = self.latest_month_link(sr_name)
                for article in articles:
                    url = self.COMMENT_BASE.format(article, 500, 100, False)
                    yield scrapy.Request(url, callback=self.comment_parse)
            if self.func == 'USER':
                author = self.kwargs['author']
                url = self.USER_BASE
                yield scrapy.Request(url.format(author), callback=self.user_parse)
            if self.func == 'SUBREDDIT':
                sr_name = self.kwargs['srname']
                yield scrapy.Request(self.SUBREDDIT_BASE.format(sr_name), callback=self.subreddit_parse)
            if self.func == 'HISTORY':
                username = self.kwargs['username']
                for index, url in self.USER_HISTORY_BASE:
                    yield scrapy.Request(url.format(username), callback=self.history_parse,
                                         meta={'base': url, 'index': index, 'username': username})
        except KeyError:
            self.logger.error('required argument missed')

    def link_parse(self, response):
        res_data = json.loads(response.body_as_unicode())
        self.logger.info('[func] link parse [url] {0}'.format(response.url))
        after = None
        url = response.meta['base']
        srname = response.meta['srname']
        try:
            after = res_data['data']['after']
        except KeyError:
            self.logger.info('key error occur when get after')
        if after is not None:
            yield scrapy.Request(url.format(srname) + '&after={0}'.format(after), callback=self.link_parse,
                                 meta={'base': url, 'srname': srname})
        for item in res_data['data']['children']:
            if 'data' in item:
                self.db[NeoData.REDDIT_LINK].find_one_and_update({'_id': item['data']['id']},
                                                                 {'$set': {'data': item['data']}},
                                                                 upsert=True)

    def comment_parse(self, response):
        res_data = json.loads(response.body_as_unicode())
        self.logger.info('[func] comment_parse [url] {0}'.format(response.url))
        try:
            if res_data is not None:
                for comment_tree in res_data[1]['data']['children']:
                    self.save_comment_tree(comment_tree)
        except Exception as e:
            self.logger.error('[error] comment_parse [response] {0}'.format(res_data))

    def user_parse(self, response):
        res_data = json.loads(response.body_as_unicode())
        self.logger.info('[func] user_parse [url] {0}'.format(response.url))
        if res_data is not None:
            self.db[NeoData.REDDIT_USER].find_one_and_update({'_id': res_data['data']['id']},
                                                             {'$set': {'data': res_data['data']}},
                                                             upsert=True)

    def subreddit_parse(self, response):
        res_data = json.loads(response.body_as_unicode())
        self.logger.info('[func] subreddit_parse [url] {0}'.format(response.url))
        if res_data is not None:
            self.db[NeoData.REDDIT_SUBREDDIT].find_one_and_update({'_id': res_data['data']['id']},
                                                                  {'$set': {'data': res_data['data']}},
                                                                  upsert=True)

    def history_parse(self, response):
        self.logger.info('[func] history_parse [url] {0}'.format(response.url))
        res_data = json.loads(response.body_as_unicode())
        index = response.meta['index']
        url = response.meta['url']
        username = res_data.meta['username']
        after = None
        try:
            after = res_data['data']['after']
        except KeyError:
            self.logger.error('key error when get after')
        if after is not None:
            url = url.format(username) + '&after={0}'.format(after)
            yield scrapy.Request(url, callback=self.history_parse,
                                 meta={'url': url, 'index': index, 'username': username})
        collection = NeoData.REDDIT_HISTORY_COMMENT if index == 0 else NeoData.REDDIT_HISTORY_SUBMIT
        self.db[collection].find_one_and_update({'_id': res_data['data']['id']},
                                                {'$set': {'data': res_data['data']}},
                                                upsert=True)

    def latest_month_link(self, sr_name):
        last_month = time.time() - 3600 * 24 * 30
        cursor = self.db[NeoData.REDDIT_LINK].find({'data.subreddit': sr_name, 'data.created_utc': {'$gt': last_month}})
        return [item['data']['id'] for item in cursor]

    def save_comment_tree(self, tree):
        tree['_id'] = tree['data']['id']
        if tree['data']['replies'] != '':
            replies = []
            reply_list = tree['data']['replies']['data']['children']
            for reply in reply_list:
                replies.append(reply['data']['id'])
                self.save_comment_tree(reply)
            tree['data']['replies'] = replies
        try:
            self.db[NeoData.REDDIT_COMMENT].find_one_and_update({'_id': tree['_id']},
                                                                {'$set': {'data': tree['data']}},
                                                                upsert=True)
        except Exception:
            self.logger.error('save comment tree error')
