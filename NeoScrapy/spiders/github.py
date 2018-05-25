from NeoScrapy.settings import MONGO_DATABASE, GITHUB_CLIENT_ID, GITHUB_SECRET
from NeoScrapy.db import NeoData, CLIENT
import scrapy
import json


class GithubSpider(scrapy.Spider):
    name = 'github'
    allowed_domains = ['github.com']

    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        """
        super(GithubSpider, self).__init__(*args, **kwargs)
        self.client = CLIENT
        self.db = self.client[MONGO_DATABASE]
        append = "?client_id=" + GITHUB_CLIENT_ID + '&client_secret=' + GITHUB_SECRET + '&&per_page=100'
        self.REPOS_BASE = "https://api.github.com/repos/{0}" + append
        self.CONTRIBUTORS_BASE = 'https://api.github.com/repos/{0}/contributors' + append
        self.SC_STAT = 'https://api.github.com/repos/{0}/stats/contributors' + append
        self.SCA_STAT = 'https://api.github.com/repos/{0}/stats/commit_activity' + append
        self.SCF_STAT = 'https://api.github.com/repos/{0}/stats/code_frequency' + append
        self.USER_BASE = 'https://api.github.com/user/{0}'+append
        self.kwargs = kwargs
        if 'func' in self.kwargs and self.kwargs['func'] in ['PROJECT']:
            self.func = kwargs['func']
            self.logger.info('[func] {0} kwargs {1}'.format(self.func, str(self.kwargs)))
        else:
            self.logger.error('no or not allowed func parameter supplied')

    def start_requests(self):
        try:
            if self.func == 'PROJECT':
                full_name = self.kwargs['full_name']
                with_user = self.kwargs['with_user']
                yield scrapy.Request(self.REPOS_BASE.format(full_name), callback=self.project_parse,
                                     meta={'full_name': full_name, 'with_user': with_user})
        except KeyError:
            self.logger.error('required argument missed')

    def parse(self, response):
        pass

    def project_parse(self, response):
        self.logger.info('[func] repos parse [url] {0}'.format(response.url))
        full_name = response.meta['full_name']
        with_user = response.meta['with_user']
        res_data = json.loads(response.body_as_unicode())
        res_data['_id'] = res_data['id']
        self.db[NeoData.GIT_PROJECT].find_one_and_update({"_id": res_data['id']}, {'$set': res_data}, upsert=True)
        try:
            meta_data = {
                'id': res_data['id'],
                'full_name': res_data['full_name'],
                'name': res_data['name']
            }
            if with_user:
                # 爬取该项目的贡献者的基本信息
                yield scrapy.Request(self.CONTRIBUTORS_BASE.format(full_name), callback=self.contributor_parse,
                                     meta=meta_data)
            yield scrapy.Request(self.SC_STAT.format(full_name), callback=self.sc_parse, meta=meta_data)
            yield scrapy.Request(self.SCA_STAT.format(full_name), callback=self.sca_parse, meta=meta_data)
            yield scrapy.Request(self.SCF_STAT.format(full_name), callback=self.scf_parse, meta=meta_data)
        except KeyError:
            self.logger.info('response error [res_data] {0}'.format(res_data))

    def contributor_parse(self, response):
        self.logger.info('[func] contributor parse [url] {0}'.format(response.url))
        res_data = json.loads(response.body_as_unicode())
        try:
            links = bytes.decode(response.headers['link']).split(',')
            for link in links:
                if 'rel="next"' in link:
                    next_url = link[link.find('<') + 1:link.rfind('>')]
                    yield scrapy.Request(next_url, callback=self.contributor_parse)
        except KeyError:
            pass
        for item in res_data:
            yield scrapy.Request(self.USER_BASE.format(item['id']), callback=self.user_parse)

    def user_parse(self, response):
        self.logger.info('[func] user parse [url] {0}'.format(response.url))
        res_data = json.loads(response.body_as_unicode())
        res_data['_id'] = res_data['id']
        self.db[NeoData.GIT_CONTRIBUTOR].find_one_and_update({'_id': res_data['id']}, {'$set': res_data}, upsert=True)

    def sc_parse(self, response):
        """
        stats contributors
        :param response:
        :return:
        """
        self.logger.info('[func] stats contributors parse [url] {0}'.format(response.url))
        res_data = json.loads(response.body_as_unicode())
        meta = response.meta
        item = {
            'type': 'sc',
            'project_id': meta['id'],
            'data': res_data
        }
        self.db[NeoData.GIT_STAT].find_one_and_update({'project_id': meta['id'],
                                                       'type': 'sc'},
                                                      {'$set': item},
                                                      upsert=True)

    def sca_parse(self, response):
        """
        stats commit activity
        :param response:
        :return:
        """
        self.logger.info('[func] stats commit activity parse [url] {0}'.format(response.url))
        res_data = json.loads(response.body_as_unicode())
        meta = response.meta
        item = {
            'type': 'sca',
            'project_id': meta['id'],
            'data': res_data
        }
        self.db[NeoData.GIT_STAT].find_one_and_update({'project_id': meta['id'],
                                                       'type': 'sca'},
                                                      {'$set': item},
                                                      upsert=True)

    def scf_parse(self, response):
        """
        stats code frequency
        :param response:
        :return:
        """
        self.logger.info('[func] stats code frequency parse [url] {0}'.format(response.url))
        res_data = json.loads(response.body_as_unicode())
        meta = response.meta
        item = {
            'type': 'scf',
            'project_id': meta['id'],
            'data': res_data
        }
        self.db[NeoData.GIT_STAT].find_one_and_update({'project_id': meta['id'],
                                                       'type': 'scf'},
                                                      {'$set': item},
                                                      upsert=True)
