import os
import shutil
import re
import datetime

import pytz

import google.cloud.logging
import requests


def utctime():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pttime():
    return datetime.datetime.now(pytz.timezone('US/Pacific')).isoformat()


def setup_logging():
    client = google.cloud.logging.Client()
    client.get_default_handler()
    client.setup_logging()


def get_absolute_import_name(dir_path, import_name):
    return '{}:{}'.format(dir_path, import_name)


def relative_import_name(import_name):
    return ':' not in import_name


def split_relative_import_name(import_name):
    return import_name.split(':')
    

def get_relative_import_names(import_names):
    return list(name for name in import_names if relative_import_name(name))


def list_to_str(a_list, sep=','):
    return (sep + ' ').join(a_list)


def get_filename(response):
    return re.findall('filename=(.+)', response.headers['Content-Disposition'])[0]


def download_file(url, dest_dir):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        filename = get_filename(response)
        path = os.path.join(dest_dir, filename)
        with open(path, 'wb') as out:
            shutil.copyfileobj(response.raw, out)
        return path
