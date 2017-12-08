import scrapy
import pickle
import zlib
import time
import re
import json
import pymongo
from lxml import html
from datetime import datetime
from bson.binary import Binary
from NeoScrapy.settings import MONGO_URI, MONGO_PORT, MONGO_DATABASE
from NeoScrapy.items import BitCoinTalkLink, BitCoinTalkComment, BitCoinTalkUserHistory


class BttSpider(scrapy.Spider):
    name = 'bitcointalk'
    allowed_domains = ['bitcointalk.org']

    def __init__(self, *args, **kwargs):
        """
        :param func: 必填参数，指定该spider实例的功能。
            ANNLINK : 获取announcement 模块下的所有帖子
            COMMENT : 获取帖子下的评论,必须参数 ids | array
            USER_PROFILE :  获取用户基本信息，统计信息, 必须参数 ids | array
            USER_HISTORY : 获取用户的历史足迹，必须参数 ids | array
        """
        super(BttSpider, self).__init__(*args, **kwargs)
        self.client = pymongo.MongoClient(MONGO_URI, MONGO_PORT)
        self.db = self.client[MONGO_DATABASE]
        self.ANN_LINK_URL = 'https://bitcointalk.org/index.php?board=159.'
        self.COMMENT_URL = 'https://bitcointalk.org/index.php?topic={0}'
        self.USER_PROFILE_URL = 'https://bitcointalk.org/index.php?action=profile;u={0}'
        self.USER_POST_URL = 'https://bitcointalk.org/index.php?action=profile;u={0};sa=showPosts'
        self.USER_START_URL = 'https://bitcointalk.org/index.php?action=profile;threads;u={0};sa=showPosts'
        self.USER_STAT_URL = 'https://bitcointalk.org/index.php?action=profile;u={0};sa=statPanel'
        self.page = 0
        self.latest = []
        if 'func' in kwargs and kwargs['func'] in ['ANNLINK', 'COMMENT', 'USER_PROFILE', 'USER_HISTORY']:
            self.func = kwargs['func']
        if 'ids' in kwargs:
            self.ids = kwargs['ids']

    def start_requests(self):
        if self.func == 'ANNLINK':
            scrapy.Request(self.ANN_LINK_URL, callback=self.ann_link_parse, meta={'index': 0})
        if self.func == 'COMMENT':
            link_id = self.ids
            yield scrapy.Request(self.COMMENT_URL.format(link_id), callback=self.comment_parse,
                                 meta={'index': 0, 'link_id': link_id})
        if self.func == 'USER_PROFILE':
            user_id = self.ids
            yield scrapy.Request(self.USER_PROFILE_URL.format(user_id), callback=self.user_profile_parse,
                                 meta={'user_id': user_id})
            yield scrapy.Request(self.USER_STAT_URL.format(user_id), callback=self.user_stat_parse,
                                 meta={'user_id': user_id})
            yield scrapy.Request(self.USER_START_URL.format(user_id), callback=self.user_history_parse,
                                 meta={'user_id': user_id, 'index': 0, 'start': True})
            yield scrapy.Request(self.USER_POST_URL.format(user_id), callback=self.user_history_parse,
                                 meta={'user_id': user_id, 'index': 0, 'start': False})

    def ann_link_parse(self, response):
        tree = html.fromstring(response.text)
        # index为0标识第一页，计算page总数并依次获取后续页面
        if response.meta['index'] == 0:
            # 首页数据组织方式和后续页面不同，所以xpath路径也不一样
            xpath_str = '//*[@id="bodyarea"]/div[3]/table/tr'
            page = int(tree.xpath('//*[@id="toppages"]/a[last()]')[0].text)
            for i in range(1, page):
                url = self.ANN_LINK_URL + str(i * 4) + '0'
                yield scrapy.Request(url, callback=self.ann_link_parse, meta={'index': i})
        else:
            xpath_str = '//*[@id="bodyarea"]/div[2]/table/tr'
        for tr in tree.xpath(xpath_str)[1:]:
            link = BitCoinTalkLink()
            try:
                td_list = tr.findall('td')
                link['title'] = self.text_format(td_list[2].find('*a').text)
                link['link_url'] = self.text_format(td_list[2].find('*a').attrib['href'])
                link['id'] = link['link_url'][link['link_url'].index('=') + 1:link['link_url'].rfind('.')]
                link['started_by'] = self.text_format(td_list[3].find('a').text)
                link['profile_url'] = self.text_format(td_list[3].find('a').attrib['href'])
                link['user_id'] = link['profile_url'][link['profile_url'].rfind('=') + 1:]
                link['replies'] = int(self.text_format(td_list[4].text))
                link['views'] = int(self.text_format(td_list[5].text))
            except Exception as e:
                self.logger.error('parse an single link from page {0} {1}'.format(response.url, str(e)))
            yield link

    def comment_parse_prepare(self, response):
        tree = html.fromstring(response.text)
        link_id = response.meta['link_id']
        # index为0标识第一页，计算page总数并依次获取后续页面
        # 只有一页，这时候td标签下没有<a>标签
        # 页数较少，一般小于25页时，最后一个<a>标签内容为'all',此时倒数第二个<a>标签的内容为总页数
        # 页数较多，没有'all'最后一个<a>标签的内容为总页数
        if len(tree.xpath('//*[@id="bodyarea"]/table[1]/tr/td/a')) == 0:
            page = 1
        elif tree.xpath('//*[@id="bodyarea"]/table[1]/tr/td/a[last()]')[0].text == 'All':
            page = int(tree.xpath('//*[@id="bodyarea"]/table[1]/tr/td/a[last()-1]')[0].text)
        else:
            page = int(tree.xpath('//*[@id="bodyarea"]/table[1]/tr/td/a[last()]')[0].text)
        for i in range(0, page):
            url = self.COMMENT_URL.format(link_id + '.' + str(i * 2) + '0')
            yield scrapy.Request(url, callback=self.comment_parse, meta={'index': i, 'link_id': link_id})

    def comment_parse(self, response):
        tree = html.fromstring(response.text)
        link_id = response.meta['link_id']
        for tr in tree.xpath('//*[@id="quickModForm"]/table[1]/tr'):
            comment = BitCoinTalkComment()
            # 遍历quickModForm下的每一个tr对象
            # 寻找 <td class='poster_info'>、<td class='td_headerandpost'>、<a class='message_number'>有三种情况：
            # 1.如果没有以上任何一项，则认为该条tr的内容不是我们想要的内容
            # 2.以上三条数据都可以找到，但是实际上该条数据已经被删除了，在页面是不显示的。这时判断message_url类似于：
            #   https://bitcointalk.org/index.php?topic=1509506136.msg1509506136#msg1509506136
            # 3.以上两种情况都不存在则认为该条记录为合格的数据
            try:
                poster_info_list = tr.xpath('descendant::*[@class="poster_info"]')
                td_headerandpost_list = tr.xpath('descendant::*[@class="td_headerandpost"]')
                message_list = tr.xpath('descendant::*[@class="message_number"]')
                if len(poster_info_list) == 0 or len(td_headerandpost_list) == 0 or len(message_list) == 0:
                    continue
                message_url = message_list[0].attrib['href']
                topic = message_url[message_url.index('=') + 1:message_url.rfind('.')]
                message_id = message_url[message_url.index('#') + 1:]
                if 'msg' + topic == message_id:
                    continue
                # 评论id信息
                comment['message_id'] = message_id
                comment['link_id'] = link_id
                # 左边author一列的信息
                poster_info = poster_info_list[0]
                comment['author'] = poster_info.find('b/a').text
                user_profile_url = poster_info.find('b/a').attrib['href']
                comment['user_profile_url'] = user_profile_url
                comment['user_id'] = user_profile_url[user_profile_url.rfind('=') + 1:]
                comment['grade'] = self.text_format(poster_info.find('div').text)
                for text in poster_info.itertext():
                    f_text = self.text_format(text)
                    if f_text.startswith('Activity'):
                        try:
                            comment['activity'] = int(f_text[f_text.index(':') + 2:])
                        except ValueError as e:
                            self.logger.error('parse user activity num error {0} {1}'.format(response.url, str(e)))
                # 右边poster信息
                # 每个帖子一楼是帖子内容（主贴），dom结构和后续评论的结构不同。一楼显示的时间为帖子最后修改的时间。
                hearder_post = td_headerandpost_list[0]
                if message_list[0].text == '#1':
                    comment['original'] = True
                time_str = hearder_post.xpath('descendant::*[@class="smalltext"]')[0].text_content()
                comment['time'] = self.time_format(time_str)
                comment['title'] = hearder_post.xpath('descendant::*[@class="subject"]/a/text()')[0]
                html_string = html.tostring(hearder_post.xpath('descendant::*[@class="post"]')[0])
                comment['content'] = Binary(zlib.compress(pickle.dumps(html_string)))
            except Exception as e:
                self.logger.error('comment parse error {0} {1}'.format(response.url, str(e)))
            yield comment

    def user_profile_parse(self, response):
        tree = html.fromstring(response.text)
        user = {}
        user["id"] = response.meta['user_id']
        for tr in tree.xpath('//*[@class="windowbg"]/table/tr'):
            try:
                if len(tr.findall('td')) < 2:
                    continue
                key = self.text_format(tr.findall('td/b')[0].text).replace(':', '').replace(' ', '')
                value = self.text_format(tr.findall('td')[1].text)
                if key == 'DateRegistered' or key == 'LastActive' or key == 'LocalTime':
                    value = self.time_format(value)
                if key == 'Activity' or key == 'Posts' or key == 'Age':
                    try:
                        value = int(value)
                    except Exception as e:
                        self.logger.error('transfer string to int error {0} {1}'.format(response.url, str(e)))
                user[key] = value
            except Exception as e:
                self.logger.error('parse user profile error {0} {1}'.format(response.url, str(e)))
        self.db['btt_user'].find_one_and_update({'_id': user['id']},
                                                {'$set': {'timestamp': datetime.now(), 'data': user}}, upsert=True)

    def user_stat_parse(self, response):
        tree = html.fromstring(response.text)
        user_id = response.meta['user_id']
        panels = tree.xpath('//*[@id="bodyarea"]//*[@class="windowbg2"]')
        general_stat = {}
        for tr in panels[0].xpath('table/tr'):
            try:
                key = self.text_format(tr.findall('td')[0].text)
                value = self.text_format(tr.findall('td')[1].text)
                if key == 'Total Time Spent Online:':
                    value = self.calc_total_time(value)
                else:
                    value = int(re.sub(r'[^0-9]', '', value))
                general_stat[key] = value
            except Exception as e:
                self.logger.error('parse user general stat error {0} {1}'.format(response.url, str(e)))
        post_stat = {}
        for tr in panels[2].xpath('table/tr'):
            try:
                key = self.text_format(tr.findall('td')[0].find('a').text)
                value = self.text_format(tr.findall('td')[2].text)
                post_stat[key] = int(value)
            except Exception as e:
                self.logger.error('parse user post stat error {0} {1}'.format(response.url, str(e)))
        activity_stat = {}
        for tr in panels[3].xpath('table/tr'):
            try:
                key = self.text_format(tr.findall('td')[0].find('a').text)
                value = self.text_format(tr.findall('td')[2].text).replace('%', '')
                activity_stat[key] = value
            except Exception as e:
                self.logger.error('parse user activity stat error {0} {1}'.format(response.url, str(e)))
        stat = {
            'user_id': user_id,
            'general_stat': general_stat,
            'post_stat': post_stat,
            'activity_stat': activity_stat,
            'type': 'origin_user_stat'
        }
        self.db['btt_stat'].find_one_and_update({'_id': stat['user_id']},
                                                {'$set': {'timestamp': datetime.now(), 'data': stat}}, upsert=True)

    def user_history_parse(self, response):
        tree = html.fromstring(response.text)
        user_id = response.meta['user_id']
        if response.meta['start']:
            url_base = self.USER_START_URL
        else:
            url_base = self.USER_POST_URL
        if response.meta['index'] == 0:
            if len(tree.xpath('//*[@class="catbg3"]/a[last()]')) == 0:
                page = 1
            elif tree.xpath('//*[@class="catbg3"]/a[last()]')[0].text == 'All':
                page = int(tree.xpath('//*[@class="catbg3"]/a[last()-1]')[0].text)
            else:
                page = int(tree.xpath('//*[@class="catbg3"]/a[last()]')[0].text)
            for i in range(1, page):
                yield scrapy.Request(url_base.format(user_id) + ';start={0}'.format(i * 20),
                                     callback=self.user_history_parse,
                                     meta={'user_id': user_id, 'index': i, 'start': response.meta['start']})
        tables = tree.xpath('//*[@id="bodyarea"]/table/tr/td/table')
        del tables[0]
        del tables[-1]
        for table in tables:
            post = BitCoinTalkUserHistory()
            post['start'] = response.meta['start']
            try:
                post['user_id'] = response.meta['user_id']
                post['module1'] = table.xpath('descendant::*[@class="titlebg2"]//a')[0].text
                post['module2'] = table.xpath('descendant::*[@class="titlebg2"]//a')[1].text
                post['module3'] = table.xpath('descendant::*[@class="titlebg2"]//a')[2].text
                href = table.xpath('descendant::*[@class="titlebg2"]//a')[2].attrib['href']
                post['href'] = href
                post['topic_id'] = href[href.index('=') + 1:href.rfind('.')]
                post['msg_id'] = href[href.index('#') + 1:]
                html_string = html.tostring(table.xpath('descendant::*[@class="post"]')[0])
                post['content'] = Binary(zlib.compress(pickle.dumps(html_string)))
                time_text = table.xpath('descendant::td[@class="middletext"]')[1].text.replace('on:', '')
                post['time'] = self.time_format(self.text_format(time_text))
            except Exception as e:
                self.logger.error('parse user history error {0} {1}'.format(response.url, str(e)))
            yield post

    @staticmethod
    def time_format(time_str):
        if time_str is None:
            return None
        if time_str.startswith('Today'):
            time_str = time_str.replace('Today at', time.strftime("%B %d, %Y,", time.localtime()))
        return time.mktime(time.strptime(time_str, '%B %d, %Y, %I:%M:%S %p'))

    @staticmethod
    def text_format(text):
        if text == 'N/A':
            return None
        if text is None:
            return None
        return text.replace('\n', '').replace('\t', '').strip()

    def calc_total_time(self, time_str):
        try:
            if 'days' in time_str:
                pattern = r'(\d*) days, (\d*) hours and (\d*) minutes.'
                match_obj = re.match(pattern, time_str)
                day = int(match_obj.group(1))
                hour = int(match_obj.group(2))
                minute = int(match_obj.group(3))
            elif 'hours' in time_str:
                pattern = r'(\d*) hours and (\d*) minutes.'
                match_obj = re.match(pattern, time_str)
                day = 0
                hour = int(match_obj.group(1))
                minute = int(match_obj.group(2))
            else:
                pattern = r'(\d*) minutes.'
                match_obj = re.match(pattern, time_str)
                day = 0
                hour = 0
                minute = int(match_obj.group(1))
        except Exception as e:
            self.logger.error('calc total time error ' + time_str + ' ' + str(e))
            return None
        return day * 60 * 24 + hour * 60 + minute
