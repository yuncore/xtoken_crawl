from scrapy import cmdline


cmd = 'scrapy crawl bitcointalk -a func=USER_PROFILE -a ids=149504'
cmdline.execute(cmd.split())