import datetime
import random
import string

from app.data import utils as mutils


def datetime_to_dutch_datetime_string(date):
    return mutils.datetime_to_dutch_datetime_string(date)


def formiodate_to_datetime(formio_date):
    date = datetime.datetime.strptime(':'.join(formio_date.split(':')[:2]), '%Y-%m-%dT%H:%M')
    return date


def datetime_to_formiodate(date):
    string = f"{datetime.datetime.strftime(date, '%Y-%m-%dT%H:%M')}:00+01:00"
    return string


def create_random_string(len):
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(len))

def deepcopy(table):
    if type(table) == dict:
        out = {}
        for k, v in table.items():
            if type(v) == list or type(v) == dict:
                out[k] = deepcopy(v)
            else:
                out[k] = v
    elif type(table) == list:
        out = []
        for i in table:
            if type(i) == list or type(i) == dict:
                out.append(deepcopy(i))
            else:
                out.append(i)
    else:
        out = table
    return out


def deepupdate(dst, src):
    for k, v in src.items():
        if type(v) == dict:
            deepupdate(dst[k], v)
        elif type(v) == list:
            dst[k] = deepcopy(v)
        else:
            dst[k] = v
    return dst


