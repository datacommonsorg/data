import os
import json
import aiohttp
import asyncio
from shutil import copy2
import time

# TODO allow store path without file name

def url_add_data(url: str, data: dict) -> str:
    # TODO check requests src
    # TODO encoding
    if '?' in url:
        url += '&'
    else:
        url += '?'
    url += '&'.join([f'{key}={value}' for key, value in data.items()])
    return url
    
# reconcile status
def sync_status_list(log_list: list, new_list: list, store_path: str = '~/dc_data/') -> list:
    ret_list = log_list.copy()
    file_ctr = 1
    for cur_url in new_list:
        if 'method' not in cur_url:
            cur_url['method'] = 'get'
        if cur_url['method'].casefold() == 'get' and 'data' in cur_url:
            cur_url['url'] = url_add_data(cur_url['url'], cur_url['data'])
        elif 'data' not in cur_url:
            cur_url['data'] = None
       
        # store_path default value, expand user and abs
        if 'store_path' not in cur_url:
            # TODO make the filename more relevant
            # add file name
            cur_url['store_path'] = os.path.join(store_path, f"{int(time.time())}")
        cur_url['store_path'] = os.path.expanduser(cur_url['store_path'])
        cur_url['store_path'] = os.path.abspath(cur_url['store_path'])
        os.makedirs(os.path.dirname(cur_url['store_path']), exist_ok=True)
        
        # search in status
        url_found = False
        for i, log_url in enumerate(log_list):
            is_same = False
            # same url
            if cur_url['url'] == log_url['url']:
                # same method
                if cur_url['method'] == log_url['method']:
                    # same data
                    if 'data' in cur_url and 'data' in log_url:
                        if cur_url['data'] == log_url['data']:
                            is_same = True
                    # no data
                    # TODO check
                    elif cur_url['method'].casefold() != 'get' and 'data' not in cur_url and 'data' not in log_url:
                        is_same = True
                    elif cur_url['method'].casefold() == 'get':
                        is_same = True
                    
            if is_same:
                url_found = True
                # copy the related data
                if 'http_code' in log_url:
                    cur_url['http_code'] = log_url['http_code']
                if 'force_fetch' not in cur_url: 
                    cur_url['force_fetch'] = False
                if cur_url['force_fetch']:
                    cur_url['status'] = 'pending'
                    cur_url.pop('http_code', None)
                else:
                    # check file existence
                    if os.path.isfile(cur_url['store_path']):
                        cur_url['status'] = 'ok'
                    # copy file if store_path is different and status ok
                    elif os.path.isfile(log_url['store_path']) and log_url['status'] = 'ok':
                        copy2(log_url['store_path'], cur_url['store_path'])
                        cur_url['status'] = 'ok'
                    else:
                        cur_url['status'] = 'pending'
                        cur_url.pop('http_code', None)
                ret_list[i] = cur_url
                    
        if not url_found:
            # force fetch
            if 'force_fetch' not in cur_url:
                cur_url['force_fetch'] = False
            cur_url['status'] = 'pending'
            cur_url.pop('http_code', None)
            ret_list.append(cur_url)
        
    return ret_list

# TODO create final list with only pending urls
def get_pending_url_list(url_list: list) -> list:
    pending_url_list = []
    for cur_url in url_list:
        if cur_url['status'] == 'pending':
            pending_url_list.append(cur_url)
    return pending_url_list

def chunk_list(src_list: list, chunk_size) -> list:
    list_chunked = [src_list[i:i + chunk_size] for i in range(0, len(src_list), chunk_size)]
    return list_chunked

def download_url_list(url_list: list, chunk_size: int = 50, log_dir: str = '~/dc_downloads/', delay_chunk = 1):    
    log_dir = os.path.expanduser(log_dir)
    log_dir = os.path.abspath(log_dir)

    # read existing log
    status_file = os.path.join(log_dir, 'download_status.json')
    
    status_url_list = []
    if os.path.isfile(status_file):
        status_url_list = json.load(open(status_file, 'r'))
    
    status_url_list = sync_status_list(status_url_list, url_list, log_dir)
    # TODO write updated status
    
    pending_url_list = get_pending_url_list(status_url_list)
    # url list chunking
    chunked_list = chunk_list(pending_url_list, chunk_size)

    # TODO add api key
        # callback function

    # TODO download
        # get or post request
        # status
        # store reponse
            # callback function
        # chunk delay
        # update log
        # TODO write updated status

# TODO retry



# unittest
