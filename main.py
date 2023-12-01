import requests
import re
import time
import random
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from pyecharts import options as opts
from pyecharts.charts import Map

# 这里改你的浏览器headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 '
                  'Safari/537.36 Edg/118.0.2088.61'}


"""
    格式化省份名称
    @pages: 页数
    @short: 是否短评
    @wait: 是否等待
    @wait_time: 等待时间
    :return 返回网页源代码
"""


def rename_region(region):
    const = ('河北省、山西省、吉林省、辽宁省、黑龙江省、陕西省、甘肃省、青海省'
             '山东省、福建省、浙江省、台湾省、河南省、湖北省、湖南省、江西省、'
             '江苏省、安徽省、广东省、海南省、四川省、贵州省、云南省。北京市、'
             '上海市、天津市、重庆市内蒙古自治区、新疆维吾尔自治区、宁夏回族自治区'
             '、广西壮族自治区、西藏自治区。内蒙古自治区、新疆维吾尔自治区、宁夏回族自治区'
             '、广西壮族自治区、西藏自治区。中国香港特别行政区、中国澳门特别行政区')
    if region not in const:
        return '其他'
    else:
        if region == "新疆":
            region = "新疆维吾尔自治区"
        elif region == "广西":
            region = "广西壮族自治区"
        elif region == "宁夏":
            region = "宁夏回族自治区"
        elif region in ["内蒙古", "西藏"]:
            region = region + "自治区"
        elif region in ["北京", "天津", "重庆", "上海"]:
            region = region + "市"
        elif region in ["中国香港", "中国澳门"]:
            region = region[-2:] + "特别行政区"
        else:
            region = region + "省"
        return region


"""
    获取网页源代码
    @pages: 页数
    @short: 是否短评
    @wait: 是否等待
    @wait_time: 等待时间
    :return 返回网页源代码
"""


def getsources(pages, short=True, wait=True, wait_time=5):
    anses = ""
    if short:
        for page in range(pages):
            url = "https://book.douban.com/subject/35898128/comments/?start=" + str(
                page * 20) + "&limit=20&status=P&sort=score"
            try:
                res = requests.get(url, headers=headers).text
                anses += res
            except:
                print("短评获取失败")
            if wait:
                time.sleep(wait_time)
            print("已经爬取" +  str(page + 1) + "/" + str(pages))
    else:
        for page in range(pages):
            url = "https://book.douban.com/subject/35898128/reviews?start=" + str(page * 20)
            try:
                res = requests.get(url, headers=headers).text
                anses += res
            except:
                print("长评获取失败")
            if wait:
                time.sleep(wait_time)
    return anses


"""
    解析数据, 将网页源代码解析成[昵称, 分数, 地区, 书评, 时间, 支持人数]
    @source: 网页源代码
    :return 返回一个list其中每个block都是[昵称, 分数, 地区, 书评, 时间, 支持人数]
"""


def splitInformation(source):  # 分割数据：
    soup = BeautifulSoup(source, "html.parser")
    anses = []
    li = soup.find_all(class_='comment-item')
    for item in li:
        try:
            name = re.findall('<a href=".*?" title="(.*?)">', str(item))[0]
            score = re.findall('<span class="user-stars allstar(.*?)0 rating" title=".*?"></span>', str(item))[0]
            area = re.findall('<span class="comment-location">(.*?)</span>', str(item))[0]
            content = re.findall('<span class="short">(.*?)</span>', str(item))
            times = re.findall('<a class="comment-time" href=".*?">(.*?)</a>', str(item))[0]
            vote = re.findall('<span class="vote-count" id=".*?">(.*?)</span>', str(item))[0]
            content.append(' ')
            content = content[0]
            block = [name, score, area, content, times, vote]
            anses.append(block)
        except:
            continue
    return anses

"""
    统计每个分数打分的个数
    @source: 经处理过的splitInformation的list
    :return 返回一个list分别为1,2,3,4,5分的人数
"""


def countscore(source):
    anses = [0, 0, 0, 0, 0]
    for item in source:
        anses[int(item[1]) - 1] += 1
    return anses

"""
    将打分由文字数加权统计分数
    @source: 经处理过的splitInformation的list
    @rates: 不满rates字数以[字数/rates]作为比例系数相乘
    :return 返回一个list分别为1,2,3,4,5分的加权分数
"""


def weightedcount(source, rates=50):
    anses = [0, 0, 0, 0, 0]
    for item in source:
        rate = 1
        if len(item[3]) < rates:
            rate = len(item[3]) / rates
        anses[int(item[1]) - 1] += rate
    return anses

"""
    将处理过的数据进行时间段区分,将其分成年/月/日及以前和之后的两个处理list
    @source: 经处理过的splitInformation的list
    @years: 年
    @months: 月
    @days: 日
    :return1 年/月/日及以前的list, :return2 年/月/日之后的list
"""


def timecunt(source, years=2023, months=10, days=21):  # 多少日及以前的分析
    ans_before = []
    ansAfter = []
    for item in source:
        try:
            year = int(re.findall('(.*?)-.*?', str(item[4]))[0])
            month = int(re.findall('.*?-(.*?)-.*?', str(item[4]))[0])
            day = int(re.findall('.*?-.*?-(.*?) .*?', str(item[4]))[0])
            if year <= years and month <= months and day <= days:
                ans_before.append(item)
            else:
                ansAfter.append(item)
        except:
            continue
    return ans_before, ansAfter

"""
    将一个list的数据化作小数比例数据
    @source: 一个纯数字的list
    :return 小数比例数据list
"""


def backrate(source):
    sums = 0
    for item in source:
        sums += item
    for i in range(len(source)):
        source[i] /= sums
    return source

"""
    将处理过的数据进行地区区域区分
    @source: 经处理过的splitInformation的list
    :return1 返回一个字典其key=地区,value=[a,b,c,d,e]分别代表打的分数
"""


def back_region(source):
    regions = {}
    backs = []
    backs_1, backs_2, backs_3, backs_4, backs_5 = [], [], [], [], []
    for item in source:
        region = item[2]
        if region == "":
            continue
        if region not in regions and region:
            regions[region] = [0, 0, 0, 0, 0]
            regions[region][int(item[1]) - 1] += 1
        else:
            regions[region][int(item[1]) - 1] += 1
    for item in regions:
        temp = {}
        num = 0
        for i in range(5):
            num += int(regions[item][i])
        items = rename_region(item)
        backs.append((items, num))
        backs_1.append((items, regions[item][0]))
        backs_2.append((items, regions[item][1]))
        backs_3.append((items, regions[item][2]))
        backs_4.append((items, regions[item][3]))
        backs_5.append((items, regions[item][4]))
    return backs, backs_1, backs_2, backs_3, backs_4, backs_5

"""
    将点赞前n个的评论导出
    @source: 经处理过的splitInformation的list
    @length: 前length个
    @reverse: Ture为降序,False为升序
    :return1 返回一个字典其key=地区,value=[a,b,c,d,e]分别代表打的分数
"""


def back_comment(source, length=20, reverse=True):
    anses = []
    sorted(source, key=lambda x: x[5], reverse=reverse)
    for i in range(length):
        anses.append(source[i][3])
    return anses

"""
    画一个五维的柱状图
    @data_list: 数据list
    @y_name: y坐标名字
    @title_name: 标题名字
"""


def create_bar_chart(data_list, y_name='Number of evaluators', title_name='The number of evaluators of The Space-Time Painter'):

    # Data for the five dimensions
    x_labels = ['1-Point', '2-Point', '3-Point', '4-Point', '5-Point']
    data = np.array(data_list)

    # Create a bar plot
    plt.figure(figsize=(8, 6))
    plt.bar(x_labels, data)
    plt.xlabel('Points')
    plt.ylabel(y_name)
    plt.title(title_name)

    plt.show()

"""
    画一个五维的饼图
    @data_list: 数据list
    @y_name: y坐标名字
    @title_name: 标题名字
"""


def create_pie_chart(data_list, title_name='The socre rate of evaluators of The Space-Time Painter'):

    # Data for the five dimensions
    labels = ['1-Point', '2-Point', '3-Point', '4-Point', '5-Point']

    # Create a pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(data_list, labels=labels, autopct='%1.1f%%', startangle=140, normalize=False)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(title_name)

    plt.show()


"""
    画中国分布的热力图
    @data: [(地区,数量),()...]
    @hot_max: 最大热值
"""


def create_map_chart(data, data_1, data_2, data_3, data_4, data_5, hot_max=50):
    c = (
        Map(init_opts=opts.InitOpts(width="1200px", height="741.6px"))
        .add('评价总人数分布',
             # 按顺序：省份名字及其值
             data,
             # 放在哪个地图上
             "china",
             # 是否在每个行政区上面显示这个行政区的名字
             label_opts=opts.LabelOpts(is_show=True),
             is_map_symbol_show=True,
             )
        .add('评价1分的分布',
             # 按顺序：省份名字及其值
             data_1,
             # 放在哪个地图上
             "china",
             # 是否在每个行政区上面显示这个行政区的名字
             label_opts=opts.LabelOpts(is_show=True),
             is_map_symbol_show=True,
             )
        .add('评价2分的分布',
             # 按顺序：省份名字及其值
             data_2,
             # 放在哪个地图上
             "china",
             # 是否在每个行政区上面显示这个行政区的名字
             label_opts=opts.LabelOpts(is_show=True),
             is_map_symbol_show=True,
             )
        .add('评价3分的分布',
             # 按顺序：省份名字及其值
             data_3,
             # 放在哪个地图上
             "china",
             # 是否在每个行政区上面显示这个行政区的名字
             label_opts=opts.LabelOpts(is_show=True),
             is_map_symbol_show=True,
             )
        .add('评价4分的分布',
             # 按顺序：省份名字及其值
             data_4,
             # 放在哪个地图上
             "china",
             # 是否在每个行政区上面显示这个行政区的名字
             label_opts=opts.LabelOpts(is_show=True),
             is_map_symbol_show=True,
             )
        .add('评价5分的分布',
             # 按顺序：省份名字及其值
             data_5,
             # 放在哪个地图上
             "china",
             # 是否在每个行政区上面显示这个行政区的名字
             label_opts=opts.LabelOpts(is_show=True),
             is_map_symbol_show=True,
             )
        .set_global_opts(
            # 设置热力图中的最大值是多少
            visualmap_opts=opts.VisualMapOpts(max_=hot_max, is_piecewise=True),
        )
        # 保存，以及文件名
        .render("map_china_cities.html")
    )




if __name__ == '__main__':
    weighted = 100 # 多少字数作为权重
    pages = 10 # 爬取的页数
    #经处理的datalist
    base_data = splitInformation(getsources(pages,True,False,5))
    #得分的人数
    data_peo = countscore(base_data)
    create_bar_chart(data_peo)
    #加权得分
    data_weight = weightedcount(base_data, weighted)
    create_bar_chart(data_weight, 'Weighted score',
                     'The weighted score of evaluators of The Space-Time Painter (' + str(weighted) + 'weighted)')
    #得分的人数比例
    data_peo_rate = backrate(data_peo)
    create_pie_chart(data_peo_rate)
    #加权得分比例
    data_weight_rate = backrate(data_weight)
    create_pie_chart(data_weight_rate,'The weighted socre rate of evaluators of The Space-Time Painter (' + str(weighted) + 'weighted)')
    #地区数据
    data_region, data_region_1, data_region_2, data_region_3, data_region_4, data_region_5 = back_region(base_data)
    create_map_chart(data_region, data_region_1, data_region_2, data_region_3, data_region_4, data_region_5)
    #时间分段
    base_data_before, base_data_after = timecunt(base_data)
    base_data_before_peo, base_data_after_peo = countscore(base_data_before), countscore(base_data_after)
    create_bar_chart(base_data_before_peo, 'Number of People','The number of evaluators of The Space-Time Painter before get prize')
    create_bar_chart(base_data_after_peo, 'Number of People','The number of evaluators of The Space-Time Painter after get prize')






