# -*- coding: utf-8 -*-

# Scrapy settings for NeoScrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
BOT_NAME = 'NeoScrapy'

SPIDER_MODULES = ['NeoScrapy.spiders']
NEWSPIDER_MODULE = 'NeoScrapy.spiders'

# MONGO_URI = '192.168.1.222'
# MONGO_PORT = 27017

MONGO_URI = '1o746k7976.51mypc.cn'
MONGO_PORT = 31006
MONGOUSER = 'llps'
MONGOPASSWORD = 'llps&789'

MONGO_DATABASE = 'neo_crawl_data'
MONGO_STATBASE = 'neo_stat_data'
MONGO_RELATIONBASE = 'neo_relation_data'

REDDIT_CLIENT_ID = 'htwdLJ6yD_O9oQ'
REDDIT_SECRET_KEY = '3qyClBiaXZgZm1k7ScGBbzH20VQ'
REDDIT_USER = 'divisey'
REDDIT_PASSWORD = '19950626zqw'

GITHUB_CLIENT_ID = '8e9f08e4e318c7824a7d'
GITHUB_SECRET = 'ea0029aa321894863089884f0756c7ed404da19a'

IMAGES_STORE = 'E:\coinmarketcurrencylogo'
# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'NeoScrapy (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0.5
DOWNLOAD_TIMEOUT = 5
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider downloadmiddlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {

}

# Enable or disable downloader downloadmiddlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'NeoScrapy.downloadmiddlewares.reddit_token_check.RedditTokenCheck': 200,
    'NeoScrapy.downloadmiddlewares.http_proxy.ProxyMiddleware': 250,
    'NeoScrapy.downloadmiddlewares.rotate_useragent.RotateUserAgentMiddleware': 500
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'NeoScrapy.pipelines.myImagePipeline.MyImagesPipeline': 700,
    'NeoScrapy.pipelines.mongodb.MongoPipeline': 800,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 0.5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 5
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

LOG_LEVEL = 'INFO'
# LOG_FILE = "logs/scrapy.log"

RETRY_ENABLED = True
RETRY_TIMES = 3

HTTPERROR_ALLOW_ALL = True
