import datetime
import time


# datetime时间转为字符串
def Changestr(datetime1):
    str1 = datetime1.strftime('%Y-%m-%d %H:%M:%S')
    return str1


# 字符串时间转为时间戳
def Changetime(str1):
    Unixtime = time.mktime(time.strptime(str1, '%Y-%m-%d %H:%M:%S'))
    return Unixtime


# datetime时间转为时间戳
def Changestamp(dt1):
    Unixtime = time.mktime(time.strptime(dt1.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))
    return Unixtime


# 时间戳转为datetime时间
def Changedatetime(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt


# uinx时间戳转换为本地时间
def Localtime(datetime1):
    Localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(datetime1))
    return Localtime


# 字符串时间转换函数
def Normaltime(datetime1):
    Normaltime = datetime.datetime.strptime(datetime1, '%Y-%m-%d %H:%M:%S')
    return Normaltime


def test_git():
    print('测试使用github')
    print('dfdsfdsfdf')