# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CoinMarketItem(scrapy.Item):
    name = scrapy.Field()
    symbol = scrapy.Field()
    sort = scrapy.Field()
    url = scrapy.Field()
    subreddit = scrapy.Field()


class TokenMarketItem(scrapy.Item):
    name = scrapy.Field()
    description = scrapy.Field()
    symbol = scrapy.Field()
    local_url = scrapy.Field()
    logo = scrapy.Field()
    follow = scrapy.Field()
    website = scrapy.Field()
    blog = scrapy.Field()
    white_paper = scrapy.Field()
    facebook = scrapy.Field()
    twitter = scrapy.Field()
    linkedin = scrapy.Field()
    slack = scrapy.Field()
    telegram = scrapy.Field()
    github = scrapy.Field()


class BitCoinTalkLink(scrapy.Item):
    title = scrapy.Field()
    link_url = scrapy.Field()
    id = scrapy.Field()
    started_by = scrapy.Field()
    profile_url = scrapy.Field()
    user_id = scrapy.Field()
    replies = scrapy.Field()
    views = scrapy.Field()


class BitCoinTalkComment(scrapy.Item):
    message_id = scrapy.Field()
    link_id = scrapy.Field()
    author = scrapy.Field()
    user_profile_url = scrapy.Field()
    user_id = scrapy.Field()
    grade = scrapy.Field()
    activity = scrapy.Field()
    original = scrapy.Field()
    time = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()


# 对于不确定字段的情况将所有的字段添加到data dict中
class BitCoinTalkUserProfile(scrapy.Item):
    data = scrapy.Field()


class BitCoinTalkUserStat(scrapy.Item):
    data = scrapy.Field()


class BitCoinTalkUserHistory(scrapy.Item):
    start = scrapy.Field()
    data = scrapy.Field()