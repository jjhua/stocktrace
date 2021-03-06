# -*- coding:utf-8 -*-
from lxml import etree
from lxml.html import parse
from pandas.util.testing import DataFrame
from market.models import Index, Industry, Equity
import pandas as pd
import numpy as np
import requests
import json
from datetime import timedelta, datetime
import arrow
import xlrd
import zipfile
import io
from django.conf import settings

db = settings.DB
date_format = 'YYYY-MM-DD'


# 中证指数
def csi_by_type(date='2011-05-04', data_type='zy1'):
    # http://115.29.204.48/syl/bk20180202.zip
    day = arrow.get(date, date_format).date()
    weekday = day.weekday()
    # ignore weekend
    if weekday == 5 or weekday == 6:
        return
    url = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio?date={}&type={}'.format(date, data_type)

    page = parse(url).getroot()
    # result = etree.tostring(page)
    # print(result)
    r = page.xpath('//table[@class="table-bg p_table table-bordered table-border mb-20"]');
    print(len(r))
    tree = etree.ElementTree(r[0])
    # print(etree.tostring(tree))
    html_table = etree.tostring(tree)
    dfs = pd.read_html(html_table, flavor='lxml')
    df = dfs[0]
    print(df)
    # v1 = df.iloc[1][1]
    # print(v1)
    for index, row in df.iterrows():
        name = row.iloc[0]
        value = row.iloc[1]
        print(index, name, value)
        if data_type == 'zy1':
            Index.objects(name=name, date=day).update_one(name=name, pe=value, upsert=True)
        elif data_type == 'zy2':
            Index.objects(name=name, date=day).update_one(name=name, pe_ttm=value, upsert=True)
        elif data_type =='zy3':
            Index.objects(name=name, date=day).update_one(name=name, pb=value, upsert=True)
        elif data_type =='zy4':
            Index.objects(name=name, date=day).update_one(name=name, dividend_yield_ratio=value, upsert=True)
        elif data_type =='zz1':
            # 行业静态市盈率
            Industry.objects(code=name, date=day).update_one(code=name, date=day, name=name, pe=value, upsert=True)
        elif data_type =='zz2':
            # 行业滚动市盈率
            Industry.objects(code=name, date=day).update_one(code=name, pe_ttm=value, upsert=True)
        elif data_type =='zz2':
            # 行业市净率
            Industry.objects(code=name, date=day).update_one(code=name, pb=value, upsert=True)
        elif data_type =='zz2':
            # 行业股息率
            Industry.objects(code=name, date=day).update_one(code=name, dividend_yield_ratio=value, upsert=True)


def csi(date='2011-05-04'):
    csi_by_type(date, 'zy1')
    csi_by_type(date, 'zy2')
    csi_by_type(date, 'zy3')
    csi_by_type(date, 'zy4')


def csi_all(begin_date='2017-12-28', end_date=None):
    if end_date is None:
        end_date = arrow.now().format(date_format)
    begin_arrow = arrow.get(begin_date, date_format)
    begin = begin_arrow.date()
    end = arrow.get(end_date, date_format).date()
    delta = end-begin
    print(delta.days)
    for i in range(delta.days):
        day = begin_arrow.shift(days=i).format(date_format)
        csi(day)


# 中证指数行业/个股PE
def csi_industry(date='20180212'):
    # http://115.29.204.48/syl/csi20180212.zip
    day = arrow.get(date, 'YYYYMMDD').date()
    weekday = day.weekday()
    # ignore weekend
    if weekday == 5 or weekday == 6:
        return
    url = 'http://115.29.204.48/syl/csi'+date+'.zip'
    r = requests.get(url)
    if r.status_code == 404:
        return
    # create memory file
    z = zipfile.ZipFile(io.BytesIO(r.content))
    # not extract to disk file here
    memory_unzip_files = extract_zip(z)
    for name in memory_unzip_files.keys():
        file_contents = memory_unzip_files.get(name)
        if len(file_contents) == 0:
            db.log.insert({'date': date})
            continue
        if file_contents:
            book = xlrd.open_workbook(file_contents=memory_unzip_files.get(name), encoding_override="gbk")
            print("The number of worksheets is {0} for date {}".format(book.nsheets), date)
            # print("Worksheet name(s): {0}".format(book.sheet_names()))
            for sheet in range(book.nsheets):
                sh = book.sheet_by_index(sheet)
                print("{0} {1} {2}".format(sh.name, sh.nrows, sh.ncols))
                for rx in range(sh.nrows):
                    row = sh.row(rx)
                    # print(row)
                    code = row[0].value
                    name = row[1].value
                    value = row[2].value
                    if value.replace('.', '', 1).isdigit():
                        if sheet == 0:
                            # 行业静态市盈率
                            Industry.objects(code=code, date=day).update_one(code=code, date=day, name=name, pe=value, upsert=True)
                        elif sheet == 1:
                            # 行业滚动市盈率
                            Industry.objects(code=code, date=day).update_one(code=code, pe_ttm=value, upsert=True)
                        elif sheet == 2:
                            # 行业市净率
                            Industry.objects(code=code, date=day).update_one(code=code, pb=value, upsert=True)
                        elif sheet == 3:
                            # 行业股息率
                            Industry.objects(code=code, date=day).update_one(code=code, dividend_yield_ratio=value, upsert=True)
                        elif sheet == 4:
                            # 个股数据
                            code1 = row[2].value
                            code2 = row[4].value
                            code3 = row[6].value
                            code4 = row[8].value
                            row10 = row[10].value
                            row11 = row[11].value
                            row12 = row[12].value
                            row13 = row[13].value
                            try:
                                pe = float(row10)
                            except:
                                pe = 0

                            try:
                                pe_ttm = float(row11)
                            except:
                                pe_ttm = 0

                            try:
                                pb = float(row12)
                            except:
                                pb = 0

                            try:
                                dyr = float(row13)
                            except:
                                dyr = 0
                            Equity.objects(name=name, date=day).update_one(code=code, date=day, name=name,
                                                                           code1=code1, code2=code2, code3=code3,
                                                                           code4=code4,
                                                                           pe=pe, pe_ttm=pe_ttm, pb=pb,
                                                                           dividend_yield_ratio=dyr, upsert=True)


def csi_industry_all(begin_date='20171228', end_date=None):
    if end_date is None:
        end_date = arrow.now().format(date_format)
    begin_arrow = arrow.get(begin_date, date_format)
    begin = begin_arrow.date()
    end = arrow.get(end_date, date_format).date()
    delta = end-begin
    for i in range(delta.days):
        day = begin_arrow.shift(days=i).format(date_format)
        csi_industry(day)

