from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings


def main():
    runner = CrawlerRunner(get_project_settings())
    # 'followall' is the name of one of the spiders of the project.
    d = runner.crawl('tokenmarket')
    d.addBoth(lambda _: reactor.stop())
    reactor.run()  # the script will block here until the crawling is finished


if __name__ == '__main__':
    main()