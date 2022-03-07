# Download Utilities

## requests_wrappers.py

Provides layer on top requests calls to decode the response and retry once on timeout.

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

## status_file_utils.py

Utility functions to manage and update status of the download URL list passed to `download_utils.py`. Function to sync 2 differnt URL lists is also provided.