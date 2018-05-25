from pymongo import MongoClient
from NeoScrapy.settings import MONGO_URI, MONGO_PORT, MONGOUSER, MONGOPASSWORD
CLIENT = MongoClient(MONGO_URI,
                     MONGO_PORT,
                     username=MONGOUSER,
                     password=MONGOPASSWORD,
                     authSource='admin',
                     authMechanism='SCRAM-SHA-1')


class NeoData:
    # config options
    APP_CONFIG = '_app_config_'

    # bitcointalk collections
    BTT_LINK = 'btt_link'                                   # announcement 下的所有帖子
    BTT_COMMENT = 'btt_comment'                             # 帖子下的评论
    BTT_USER = 'btt_user'                                   # 用户的基本信息
    BTT_USER_STAT = 'btt_stat'                              # 用户的统计信息，来自https://bitcointalk.org/index.php?action=profile;u={0};sa=statPanel的信息
    BTT_USER_HISTORY_POST = 'btt_history_post'              # 用户历史评论数据
    BTT_USER_HISTORY_START = 'btt_history_start'            # 用户历史发帖信息

    # github collections
    GIT_COMMIT = 'git_commit'                               # github commit 数据
    GIT_CONTRIBUTOR = 'git_contributor'                     # 对仓库产生贡献者的用户信息
                                                            # 2018/1/15 该表可以只用来存用户的信息，即git_user；用户对项目的贡献关系可以从git_stat表中得到
    GIT_PROJECT = 'git_project'                             # 项目信息
    # ....
    # github api 提供的数据统计接口
    # type：scf [stat code frequency] | sc [stats contributors] | sca [stat comment activity]
    GIT_STAT = 'git_stat'

    # reddit collections
    REDDIT_LINK = 'reddit_link'                             # reddit中的发帖信息
    REDDIT_COMMENT = 'reddit_comment'                       # reddit中的评论信息
    REDDIT_SUBREDDIT = 'reddit_subreddit'                   # subreddit基本信息
    REDDIT_USER = 'reddit_user_basic_info'                  # reddit用户基本信息
    REDDIT_HISTORY_COMMENT = 'reddit_history_comment'       # 用户评论的历史信息
    REDDIT_HISTORY_SUBMIT = 'reddit_history_submitted'      # 用户提交(发帖)的历史信息

    # tokenmarket currencies
    TOKENMARKET_CURRENCIES = 'tokenmarket_currency'         # tokenmarket中货币的信息

    # coinmarket currencies
    COINMARKET_CURRENCIES = 'coinmarket_currency'           # coinmarket中货币的基本信息
    COINMARKET_HISTORY_PRICE = 'coinmarket_history_currency'    # coinmarket中货币的历史价格信息
    COINMARKET_TOTAL_MARKET_CAP = 'coinmarket_total_market_cap'     # coinmarket中历史市场cap数据

    COINDESK_NEWS = 'coindesk_news'               # coindesk 中的资讯信息

    ICOHOLDER_BASE = 'icoholder_base'             # 从ico holder中获取的货币ico筹集的时间和总金额

    # relation collections
    RELATION_CURRENCY_REDDIT = 'relation_currency_reddit'  # 保存reddit和currency之间的对应关系
    RELAITON_CURRENCY_GITHUB = 'relation_currency_github'  # 保存gitbub和currency之间的对应关系
    RELATION_CURRENCY_BTT = 'relation_currency_btt'  # 保存bitcointalk和currency之间的对应关系



