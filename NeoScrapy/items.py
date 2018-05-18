# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CoinMarketItem(scrapy.Item):
    name = scrapy.Field()
    id = scrapy.Field()
    symbol = scrapy.Field()
    sort = scrapy.Field()
    subreddit = scrapy.Field()
    url = scrapy.Field()
    logo_url = scrapy.Field()
    logo_img_name = scrapy.Field()
    website  = scrapy.Field()
    topic_id = scrapy.Field()
    explorer = scrapy.Field()
    github_repo = scrapy.Field()
    github_project = scrapy.Field()
    message_board = scrapy.Field()
    chat = scrapy.Field()


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
    quote_id = scrapy.Field()


class BitCoinTalkUserHistory(scrapy.Item):
    start = scrapy.Field()
    data = scrapy.Field()
    user_id = scrapy.Field()
    module1 = scrapy.Field()
    module2 = scrapy.Field()
    module3 = scrapy.Field()
    href = scrapy.Field()
    topic_id = scrapy.Field()
    msg_id = scrapy.Field()
    content = scrapy.Field()
    time = scrapy.Field()
    quote_id = scrapy.Field()