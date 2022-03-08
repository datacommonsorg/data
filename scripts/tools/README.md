# Download Utilities

## download_utils.py

Basic functions to make parallel URL requests using `aiohttp` package.

The functions accept a list of dict objects with relevant information. Each dict can have following keys:

- `url` (mandatory) - The URL destination for request.
- `store_path` (mandatory) - The path to store the response.
- `force_fetch` (optional) - Boolean value to force request even if the response file exists.
- `method` (optional) - Request method to be used. **NOTE: Only `get` is currently supported.**
- `status` - Status of the request. Can take any value from `['pending', 'ok', 'fail', 'fail_http']`. Generated based on the response.
- `http_code` - String version of the HTTP response code.
- `data` - Payload for `POST` request. **NOTE: Not supported currently.**

The availble methods accept callback functions to:

- Attach API key information to the URL.
- Process and store the response. **NOTE: The response needs to be stored in the callback function. By default the response is NOT stored. Simplest callback function would parse to required format and store it to the destination path.**

### Example code

```
from download_utils import download_url_list, async_save_resp_json

url_list = [{
            'url': 'https://httpbin.org/get?a=1',
            'store_path': './tmp/1.json',
            'status': 'pending'
        }, {
            'url': 'https://httpbin.org/get?b=2',
            'store_path': './tmp/2.json'
        }, {
            'url': 'https://httpbin.org/status/204',
            'store_path': './tmp/3.json'
        }, {
            'url': 'https://httpbin.org/status/404',
            'store_path': './tmp/4.json',
            'status': 'pending'
        }]

        fail_ctr = download_url_list(url_list, None, '', async_save_resp_json, {})
```

## status_file_utils.py

Utility functions to manage and update status of the download URL list passed to `download_utils.py`. Function to sync 2 differnt URL lists is also provided.