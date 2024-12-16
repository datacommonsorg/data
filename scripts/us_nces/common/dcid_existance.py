import datacommons as dc
import time
import logging
import requests_cache
import urllib

dc.utils._API_ROOT = 'http://api.datacommons.org'


def dc_api_wrapper(function,
                   args: dict,
                   retries: int = 3,
                   retry_secs: int = 5,
                   use_cache: bool = False,
                   api_root: str = None):
    '''Returns the result from the DC APi call function.
    Retries the function in case of errors.

    Args:
      function: The DataCOmmons API function.
      args: dictionary with ann the arguments fr the DataCommons APi function.
      retries: Number of retries in case of HTTP errors.
      retry_sec: Interval in seconds between retries for which caller is blocked.
      use_cache: If True, uses request cache for faster response.
      api_root: The API server to use. Default is 'http://api.datacommons.org'.
         To use autopush with more recent data, set it to 'http://autopush.api.datacommons.org'

    'Returns:
      The response from the DataCommons API call.
    '''
    if api_root:
        dc.utils._API_ROOT = api_root
        logging.debug(f'Setting DC API root to {api_root} for {function}')
    if not retries or retries <= 0:
        retries = 1
    if not requests_cache.is_installed():
        requests_cache.install_cache(expires_after=300)
    cache_context = None
    if use_cache:
        cache_context = requests_cache.enabled()
        logging.debug(f'Using requests_cache for DC API {function}')
    else:
        cache_context = requests_cache.disabled()
        logging.debug(f'Using requests_cache for DC API {function}')
    with cache_context:
        for attempt in range(0, retries):
            try:
                logging.debug(
                    f'Invoking DC API {function} with {args}, retries={retries}'
                )
                return function(**args)
            except KeyError:
                # Exception in case of API error.
                return None
            except urllib.error.URLError:
                # Exception when server is overloaded, retry after a delay
                if attempt >= retries:
                    raise RuntimeError
                else:
                    logging.debug(
                        f'Retrying API {function} after {retry_secs}...')
                    time.sleep(retry_secs)
    return None


def dc_api_batched_wrapper(function, dcids: list, args: dict,
                           config: dict) -> dict:
    '''Returns the dictionary result for the function cal on all APIs.
  It batches the dcids to make multiple calls to the DC API and merges all results.

  Args:
    function: DC API to be invoked. It should have dcids as one of the arguments
      and should return a dictionary with dcid as the key.
    dcids: List of dcids to be invoked with the function.
    args: Additional arguments for the function call.
    config: dictionary of DC API configuration settings.
      The supported settings are:
        dc_api_batch_size: Number of dcids to invoke per API call.
        dc_api_retries: Number of times an API can be retried.
        dc_api_retry_sec: Interval in seconds between retries.
        dc_api_use_cache: Enable/disable request cache for the DC API call.
        dc_api_root: The server to use fr the DC API calls.

  Returns:
    Merged function return values across all dcids.
  '''
    api_result = {}
    index = 0
    num_dcids = len(dcids)
    api_batch_size = config.get('dc_api_batch_size', 10)
    logging.info(
        f'Calling DC API {function} on {len(dcids)} dcids in batches of {api_batch_size} with args: {args}...'
    )
    while index < num_dcids:
        #  dcids in batches.
        dcids_batch = [
            # strip_namespace(x) for x in dcids[index:index + api_batch_size]
            x for x in dcids[index:index + api_batch_size]
        ]
        index += api_batch_size
        args['dcids'] = dcids_batch
        batch_result = dc_api_wrapper(function, args,
                                      config.get('dc_api_retries', 3),
                                      config.get('dc_api_retry_secs', 5),
                                      config.get('dc_api_use_cache', False),
                                      config.get('dc_api_root', None))
        if batch_result:
            api_result.update(batch_result)
            logging.debug(f'Got DC API result for {function}: {batch_result}')
    return api_result


def dc_api_get_defined_dcids(dcids: list, config: dict) -> dict:
    '''Returns a dict with dcids mapped to list of types in the DataCommons KG.
       Uses the property_value API to lookup 'typeOf' for each dcid.
       dcids not defined in KG are dropped in the response.
    '''
    api_function = dc.get_property_values
    args = {
        'prop': 'typeOf',
        'out': True,
    }
    api_result = dc_api_batched_wrapper(api_function, dcids, args, config)
    response = {}
    # Remove empty results for dcids not defined in KG.
    for dcid in dcids:
        if dcid in api_result and api_result[dcid]:
            response[dcid] = True
        else:
            response[dcid] = False
    return response