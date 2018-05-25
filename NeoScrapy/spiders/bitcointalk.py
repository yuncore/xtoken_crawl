import scrapy
import time
import re
import pymongo
from NeoScrapy.db import NeoData
from lxml import html
from datetime import datetime
from NeoScrapy.settings import MONGO_DATABASE
from NeoScrapy.db import CLIENT
from NeoScrapy.items import BitCoinTalkLink, BitCoinTalkComment, BitCoinTalkUserHistory


class BttSpider(scrapy.Spider):
    name = 'bitcointalk'
    allowed_domains = ['bitcointalk.org']

    def __init__(self, *args, **kwargs):
        """
        func: 必填参数，指定该spider实例的功能。
            ANNLINK : 获取announcement 模块下的所有帖子
            COMMENT : 获取帖子下的评论,必须参数 ids | array
            USER :  获取用户基本信息，统计信息, 必须参数 ids | array
        force: 可选参数，当force为true时强制获取所有的时间段内的评论，否则截止到数据库中最新的时间为止
        """
        super(BttSpider, self).__init__(*args, **kwargs)
        self.client = CLIENT
        self.db = self.client[MONGO_DATABASE]
        self.ANN_LINK_URL = 'https://bitcointalk.org/index.php?board=159.'
        self.COMMENT_URL = 'https://bitcointalk.org/index.php?topic={0}'
        self.USER_PROFILE_URL = 'https://bitcointalk.org/index.php?action=profile;u={0}'
        self.USER_POST_URL = 'https://bitcointalk.org/index.php?action=profile;u={0};sa=showPosts'
        self.USER_START_URL = 'https://bitcointalk.org/index.php?action=profile;threads;u={0};sa=showPosts'
        self.USER_STAT_URL = 'https://bitcointalk.org/index.php?action=profile;u={0};sa=statPanel'
        self.latest = 0
        if 'func' in kwargs and kwargs['func'] in ['ANNLINK', 'COMMENT', 'USER']:
            self.func = kwargs['func']
            self.logger.info('[func] {0}'.format(self.func))
        if 'ids' in kwargs:
            self.ids = kwargs['ids']
            self.logger.info('[ids] {0}'.format(self.ids))
        if 'force' in kwargs:
            if kwargs['force'] == 'True':
                self.force = True
            else:
                self.force = False
            self.logger.info('[force] {0}'.format(self.force))

    def start_requests(self):
        if self.func == 'ANNLINK':
            yield scrapy.Request(self.ANN_LINK_URL, callback=self.ann_link_parse, meta={'index': 0})
        if self.func == 'COMMENT':
            link_id = self.ids
            yield scrapy.Request(self.COMMENT_URL.format(link_id), callback=self.comment_parse_prepare,
                                 meta={'index': 0, 'link_id': link_id})
        if self.func == 'USER':
            user_id = self.ids
            yield scrapy.Request(self.USER_PROFILE_URL.format(user_id), callback=self.user_profile_parse,
                                 meta={'user_id': user_id})
            # btt的user stat 页面已经坏掉了
            # yield scrapy.Request(self.USER_STAT_URL.format(user_id), callback=self.user_stat_parse,
            #                     meta={'user_id': user_id})
            # 现在不需要获取用户的全部历史数据
            # yield scrapy.Request(self.USER_START_URL.format(user_id), callback=self.user_history_parse_prepare,
            #                      meta={'user_id': user_id, 'index': 0, 'start': True})
            # yield scrapy.Request(self.USER_POST_URL.format(user_id), callback=self.user_history_parse_prepare,
            #                      meta={'user_id': user_id, 'index': 0, 'start': False})

    def ann_link_parse(self, response):
        self.logger.info('[func] ann_link_parse [url] {0}'.format(response.url))
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
        """
        计算总页数，从最后一页开始下载
        :param response:
        :return:
        """
        tree = html.fromstring(response.text)
        link_id = response.meta['link_id']
        # index为0标识第一页，计算page总数并依次获取后续页面
        # 只有一页，这时候td标签下没有<a>标签
        # 页数较少，一般小于25页时，最后一个<a>标签内容为'all',此时倒数第二个<a>标签的内容为总页数
        # 页数较多，没有'all'最后一个<a>标签的内容为总页数
        # 特殊情况下，btt页面的页数table上面会有一个投票的table，这时计算的页数就不准了。所以需要判断第一bodyarea的第一个table是否是投票table
        table_index = 1
        src = tree.xpath('//*[@id="bodyarea"]/table[1]/tr/td/img/@src')
        if len(src) > 0 and src[0] == 'https://bitcointalk.org/Themes/custom1/images/topic/normal_poll.gif':
            table_index = 2
        if len(tree.xpath('//*[@id="bodyarea"]/table[{0}]/tr/td/a'.format(table_index))) == 0:
            page = 1
        elif tree.xpath('//*[@id="bodyarea"]/table[{0}]/tr/td/a[last()]'.format(table_index))[0].text == 'All':
            page = int(tree.xpath('//*[@id="bodyarea"]/table[{0}]/tr/td/a[last()-1]'.format(table_index))[0].text)
        else:
            page = int(tree.xpath('//*[@id="bodyarea"]/table[{0}]/tr/td/a[last()]'.format(table_index))[0].text)
        self.latest = self.latest_comment(link_id)
        url = self.COMMENT_URL.format(link_id + '.' + str(page * 2) + '0')
        yield scrapy.Request(url, callback=self.comment_parse, meta={'index': page, 'link_id': link_id})

    def latest_comment(self, link_id):
        """
        从数据数据库中查询最新的一条评论，返回该条评论的时间戳
        :param link_id:
        :return:
        """
        try:
            return self.db[NeoData.BTT_COMMENT].find({'data.link_id': link_id}).sort([('data.time', pymongo.DESCENDING)]).limit(1)[1]['data']['time']
        except IndexError:
            return 0

    def comment_parse(self, response):
        """
        提取页面信息，将提取到的记录与数据库中最新一条记录的时间对比，确定是否需要发送下一条请求
        :param response:
        :return:
        """
        self.logger.info('[func] comment_parse [url] {0} [page] {1}'.format(response.url, response.meta['index']))
        tree = html.fromstring(response.text)
        link_id = response.meta['link_id']
        next_request = True
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
                content_aly = self.aly_content(hearder_post.xpath('descendant::*[@class="post"]')[0])
                comment['content'] = content_aly['content']
                comment['quote_id'] = content_aly['quote_id']
                if comment['time'] < self.latest:
                    next_request = False
            except Exception as e:
                self.logger.error('comment parse error {0} {1}'.format(response.url, str(e)))
            yield comment
        page = response.meta['index'] - 1
        if page >= 0 and (self.force or next_request):
            url = self.COMMENT_URL.format(link_id + '.' + str(page * 2) + '0')
            yield scrapy.Request(url, callback=self.comment_parse, meta={'index': page, 'link_id': link_id})

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
                        self.logger.info('transfer string to int error key = {0}'.format(key))
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
        if panels is None:
            return
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

    def user_history_parse_prepare(self, response):
        tree = html.fromstring(response.text)
        start = response.meta['start']
        user_id = response.meta['user_id']
        url_base = self.USER_START_URL if start else self.USER_POST_URL
        if len(tree.xpath('//*[@class="catbg3"]/a[last()]')) == 0:
            page = 1
        elif tree.xpath('//*[@class="catbg3"]/a[last()]')[0].text == 'All':
            page = int(tree.xpath('//*[@class="catbg3"]/a[last()-1]')[0].text)
        else:
            page = int(tree.xpath('//*[@class="catbg3"]/a[last()]')[0].text)
        self.latest = self.history_latest(user_id, start)
        url = url_base.format(user_id) + ';start={0}'.format(0 * 20)
        yield scrapy.Request(url, callback=self.user_history_parse,
                             meta={'user_id': user_id, 'index': 0, 'url_base': url_base, 'page': page, 'start': start})

    def history_latest(self, user_id, start):
        col = 'btt_history_start' if start else 'btt_history_post'
        try:
            return self.db[col].find({'data.user_id': user_id}).sort([('data.time', pymongo.DESCENDING)]).limit(1)['data'][time]
        except Exception:
            return 0

    def user_history_parse(self, response):
        self.logger.info('[func] user_history_parse [url] {0} [page] {1}'.format(response.url, response.meta['index']))
        tree = html.fromstring(response.text)
        user_id = response.meta['user_id']
        next_request = True
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
                content_aly = self.aly_content(table.xpath('descendant::*[@class="post"]')[0])
                post['content'] = content_aly['content']
                post['quote_id'] = content_aly['quote_id']
                time_text = table.xpath('descendant::td[@class="middletext"]')[1].text.replace('on:', '')
                post['time'] = self.time_format(self.text_format(time_text))
                if post['time'] < self.latest:
                    next_request = False
            except Exception as e:
                self.logger.error('parse user history error {0} {1}'.format(response.url, str(e)))
            yield post
        page = response.meta['page']
        index = response.meta['index']
        url_base = response.meta['url_base']
        start = response.meta['start']
        if index < page and (self.force or next_request):
            url = url_base.format(user_id) + ';start={0}'.format((index + 1) * 20)
            yield scrapy.Request(url, callback=self.user_history_parse,
                                 meta={'user_id': user_id, 'index': (index+1), 'url_base': url_base, 'page': page, 'start': start})

    def aly_content(self, tree):
        text = self.extract_comment(tree)
        quote_id = None
        try:
            quote = tree.xpath('child::*[@class="quoteheader"]/a')[0].attrib['href']
            quote_id = quote[quote.index('#') + 1:]
        except (IndexError, ValueError):
            pass
        finally:
            return {'content': text, 'quote_id': quote_id}

    @staticmethod
    def extract_comment(tree):
        s = tree.text if tree.text is not None else ''
        for item in tree.getchildren():
            if item.text is not None:
                s += item.text
            elif item.tail is not None:
                s += item.tail
        return s

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
