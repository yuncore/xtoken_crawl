from scrapy import cmdline


# cmd = 'scrapy crawl bitcointalk -a func=COMMENT -a ids=1365894 -a force=False'
# cmd = 'scrapy crawl bitcointalk -a func=USER -a ids=6964 -a force=False'
# cmd = 'scrapy crawl bitcointalk -a func=ANNLINK -a force=False'
# cmd = 'scrapy crawl reddit -a func=SUBREDDIT -a srname=NEO'
# cmd = 'scrapy crawl reddit -a func=LINK -a srname=NEO'
# cmd = 'scrapy crawl reddit -a func=COMMENT -a srname=garlicoin'
# cmd = 'scrapy crawl coinmarketcap -a func=TOTAL_MARKET'
# cmd = 'scrapy crawl coinmarketcap -a func=HISTORY_PRICE -a currency_id=gbcgoldcoin'
# cmd = "scrapy crawl github -a func=PROJECT -a full_name=ethereum/ethereumj -a with_user=True"
# cmd = 'scrapy crawl coindesk'
# cmd = 'scrapy crawl icoholder'
cmd = 'scrapy crawl ethfans'
cmdline.execute(cmd.split())
