try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests
import tornado
import ujson
import pandas as pd
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import lru_cache
from .log_utils import log


def parse_args(argv):
    args = []
    kwargs = {}
    for arg in argv:
        if '--' not in arg and '-' not in arg:
            log.debug('ignoring argument: %s', arg)
            continue
        if '=' in arg:
            k, v = arg.replace('-', '').split('=')
            kwargs[k] = v
        else:
            args.append(arg.replace('-', ''))
    return args, kwargs


def parse_body(req, **fields):
    try:
        data = tornado.escape.json_decode(req.body)
    except ValueError:
        data = {}
    return data


def safe_get(path, *args, **kwargs):
    try:
        log.debug('GET: %s' % path)
        resp = requests.get(path, *args, **kwargs).text
        # log.debug('GET_RESPONSE: %s' % resp)
        return ujson.loads(resp)
    except ConnectionRefusedError:
        return {}


def safe_post(path, *args, **kwargs):
    try:
        log.debug('POST: %s' % path)
        resp = requests.post(path, *args, **kwargs).text
        # log.debug('POST_RESPONSE: %s' % resp)
        return ujson.loads(resp)
    except ConnectionRefusedError:
        return {}


def safe_post_cookies(path, *args, **kwargs):
    try:
        log.debug('POST: %s' % path)
        resp = requests.post(path, *args, **kwargs)
        # log.debug('POST_RESPONSE: %s' % resp.text)
        return ujson.loads(resp.text), resp.cookies
    except ConnectionRefusedError:
        return {}, None


def construct_path(host, method):
    return urljoin(host, method)


@lru_cache(1)
def today():
    '''today starts at 4pm the previous close'''
    today = date.today()
    return datetime(year=today.year, month=today.month, day=today.day)


@lru_cache(1)
def this_week():
    '''start of week'''
    return today() - timedelta(days=datetime.today().isoweekday() % 7)


@lru_cache(1)
def last_close():
    '''last close'''
    today = date.today()
    close = datetime(year=today.year, month=today.month, day=today.day, hour=16)

    if datetime.now().hour < 16:
        close -= timedelta(days=1)
        if close.weekday() == 5:  # saturday
            return close - timedelta(days=1)
        elif close.weekday() == 6:  # sunday
            return close - timedelta(days=2)
        return close
    return close


@lru_cache(1)
def yesterday():
    '''yesterday is anytime before the previous 4pm close'''
    today = date.today()

    if today.weekday() == 0:  # monday
        return datetime(year=today.year, month=today.month, day=today.day) - timedelta(days=3)
    elif today.weekday() == 6:  # sunday
        return datetime(year=today.year, month=today.month, day=today.day) - timedelta(days=2)
    return datetime(year=today.year, month=today.month, day=today.day) - timedelta(days=1)


@lru_cache(1)
def last_month():
    '''last_month is one month before today'''
    today = date.today()
    last_month = datetime(year=today.year, month=today.month, day=today.day) - relativedelta(months=1)

    if last_month.weekday() == 5:
        last_month -= timedelta(days=1)
    elif last_month.weekday() == 6:
        last_month -= timedelta(days=2)
    return last_month


@lru_cache(1)
def six_months():
    '''six_months is six months before today'''
    today = date.today()
    six_months = datetime(year=today.year, month=today.month, day=today.day) - relativedelta(months=6)

    if six_months.weekday() == 5:
        six_months -= timedelta(days=1)
    elif six_months.weekday() == 6:
        six_months -= timedelta(days=2)
    return six_months


@lru_cache(1)
def never():
    '''long long time ago'''
    return datetime(year=1, month=1, day=1)


def append(df1, df2):
    merged = pd.concat([df1, df2])
    return merged[~merged.index.duplicated(keep='first')]