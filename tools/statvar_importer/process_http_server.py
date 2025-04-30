# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Class to create a web interface for a python script with commandline flags.

Creates a web form that accepts POST requests and launches
the python script on command line as a sub-process and
streams back the output on STDOUT and STDERR.

To create a web form for any script with commandline args, use it as follows:
  import process_http_server

  from absl import app
  from absl import flags

  _FLAGS = flags.FLAGS

  # FLAGs converted to HTML form inputs and passed to script invoked.
  flags.DEFINE_string('input_file', '', 'File to process')

  ...

  def main(_):
      # Create a web interface the script with a form for command line args
      # that don't begin with 'http':
      #   File to process: < input-text-box >
      #   <Submit>
      # On Submit, this script is invoked without the http_port arg
      # with other args set from the form.
      process_http_server.run_http_server(script=__file__)

      # Run the process with command line parameters.
      MyProcess()

  if __name__ == '__main__':
    app.run(main)


  Run it with commandline flags:
    python my_process.py --my_flag1=123 --my_flag2=def --http_port=8100

  This will create a form on localhost:8100 with an input for input_sheet.

  On form submit, the following script will be run and
  its stdout/strerr is returned:
    python my_process.py --my_flag1=123 --my_flag2=def
    --input_file=<form-value>
"""

import cgi
from http import server
import os
import select
import socket
import subprocess
import sys
import threading
import time
from urllib import parse

from absl import app
from absl import flags
from absl import logging

_FLAGS = flags.FLAGS

flags.DEFINE_integer('http_port', 0, 'HTTP port to listen for URLs.')
flags.DEFINE_integer(
    'http_server_threads',
    10,
    'Number of http listener threads for simultaneous requests.',
)
flags.DEFINE_string('http_config', '',
                    'File with configurations for the HTTP server.')
flags.DEFINE_integer(
    'http_server_timeout',
    86400 * 365,
    'Maximum duration in seconds to run the web server.',
)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from config_map import ConfigMap

# Config for HTTP Web Server.
# Note: this is modified to the form required at run time.
# Only one call to run_http_server() is supported.
_HTTP_CONFIG = {
    # List of Forms
    'script':
        '',  # Python script to be invoked when form is submitted.
    'forms': [
        # Form settings for one form.
        {
            'form_title':
                'SampleForm',  # Title for the form
            'form_input': [
                # List of form inputs
                {
                    'description':
                        ('Sample text input'),  # Text before the input.
                    'name': 'input',  # Form input element id.
                    'type': 'text',  # Type of input.
                },
            ],
        },
    ],
}


# Class for a Web server wrapper for a python script.
class ProcessHandler(server.SimpleHTTPRequestHandler):

    def do_GET(self):
        """Returns a HTML form to the client."""
        # Send the HTML form
        logging.info(f'HTTP GET: Generating form for config: {_HTTP_CONFIG}')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        form_config = _HTTP_CONFIG.get('forms', [{}])[0]
        self.wfile.write(bytes(self.get_html_form(form_config), 'utf-8'))

    def do_POST(self):
        """Returns a HTML page with output from the script invoked for the form parameters."""
        # Get the form inputs to be used as command line arguments.
        form_config = _HTTP_CONFIG.get('forms', [{}])[0]
        form_data = self.parse_form_data(form_config)
        # Create args for child process, copying over any scripts args.
        args = ['python']
        sys_args = sys.argv
        script = _HTTP_CONFIG.get('script', None)
        if script:
            args.append(script)
            sys_args = sys_args[1:]
        # Add args from this invocation that doesn't begin with 'http'
        # All commandline flags that begin with 'http' are for the server
        # Any other params are for the processing script to be invoked.
        for arg in sys_args:
            if arg and not arg.startswith('--http'):
                args.append(arg)
        # Add args from the form that can override this script's invoked args.
        for key, value in form_data.items():
            args.append(f'--{key}={value}')
        cmd = ' '.join(args)

        # Fork a process to run the script with the args from the form
        logging.info(f'Launching process: "{cmd}"')
        start_time = time.perf_counter()
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        # Stream the output back to the client
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(bytes(f'Running script: "{cmd}"\n\n', 'utf-8'))
        for line in process.stdout:
            logging.info(f'Process stdout: {line}')
            self.wfile.write(bytes(line))
        for line in process.stderr:
            logging.info(f'Process stderr: {line}')
            self.wfile.write(bytes(line))

        end_time = time.perf_counter()
        return_code = process.returncode
        end_msg = (
            f'Completed script: "{cmd}", Return code: {return_code}, time:'
            f' {end_time - start_time:.3f} secs.\n')
        self.wfile.write(bytes(end_msg, 'utf-8'))
        logging.info(end_msg)

    def get_html_form(self, form_config: dict = {}) -> str:
        """Returns the HTML form for the config."""
        form_title = form_config.get('form_title', '')
        if not form_title:
            script = _HTTP_CONFIG.get('script', sys.argv[0])
            if script:
                form_title = os.path.basename(script)
        form_action = form_config.get('action', '/')
        form_params_html = ''
        for param in form_config.get('form_input', []):
            # Add HTML input tag for the form parameter.
            description = param.get('description', '')
            name = param.get('name', 'input')
            param_type = param.get('type', 'text')
            form_input = f"""
   <tr>
      <td>{description}</td>
      <td><input type="{param_type}" name="{name}"></td>
    </tr>
"""
            form_params_html += form_input
        form_params_html += f"""   <tr>
      <td colspan="2" style="text-align:center; vertical-align:middle">
        <input type="submit" value="Submit">
      </td>
    </tr>"""

        form_html = f"""
<!DOCTYPE html>
<html>
<head>
  <title>{form_title}</title>
</head>
<body>
  <form action="{form_action}" method="POST">
    <table>
     {form_params_html}
    </table>
  </form>
</body>
</html>"""
        return form_html

    def parse_form_data(self, form_config: dict = {}):
        """Returns a dictionary with form input name as key and value from POST data

    for all the form inputs in the form_config.
    """
        form = cgi.FieldStorage(fp=self.rfile,
                                headers=self.headers,
                                environ={'REQUEST_METHOD': 'POST'})
        form_input = {}
        for param in form_config.get('form_input', {}):
            param_name = param.get('name', '')
            if param_name:
                value = form.getvalue(param_name)
                if value:
                    form_input[param_name] = value
        logging.info(f'Got HTTP POST input: {form_input}')
        return form_input


# Class to launch a listener per thread.
# Handler has to support methods such as do_GET() or do_POST() to support
# requests.
class ThreadedHTTPListner(threading.Thread):

    def __init__(self, sock, thread_num, addr, handler):
        threading.Thread.__init__(self)
        self._sock = sock
        self._thread_num = thread_num
        self._addr = addr
        self._handler = handler
        self.daemon = True
        self._httpd = None
        self.start()

    def run(self):
        self._httpd = server.HTTPServer(self._addr, self._handler, False)
        # Prevent the HTTP server from re-binding every handler.
        # https://stackoverflow.com/questions/46210672/
        self._httpd.socket = self._sock
        self._httpd.server_bind = self.server_close = lambda self: None
        logging.info(
            f'Created http listener {self._thread_num} with {self._handler} on'
            f' address {self._addr}')
        self._httpd.serve_forever()

    def shutdown(self):
        if self._httpd is not None:
            logging.info(f'Shutting down listener {self._thread_num}')
            self._httpd.shutdown()
            logging.info(f'Listener {self._thread_num} terminated')
            self._httpd = None


# WebServer with multiple threads to handle requests in parallel.
class ThreadedHTTPServer:

    def __init__(self, http_port, handler, num_threads: int = 10):
        self._num_threads = num_threads
        self._handler = handler
        # Create a single socket for all threads.
        self._addr = ('', http_port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(self._addr)
        self._sock.listen(5)

    def serve_forever(self, timeout: int = sys.maxsize):
        """Launch the server with listener threads and block."""
        threads = []
        for i in range(self._num_threads):
            logging.info(f'Launching thread: {i}')
            thread = ThreadedHTTPListner(self._sock, i, self._addr,
                                         self._handler)
            threads.append(thread)

        # Block forever.
        time.sleep(timeout)

        # Shutdown the server threads.
        for thread in threads:
            thread.shutdown()


def _get_form_config(config: dict = None) -> dict:
    """Returns the config for the form."""
    if not config:
        config = _HTTP_CONFIG
    if 'forms' not in config:
        config['forms'] = [{}]
    return config.get('forms', [{}])[0]


def run_http_server(
    http_port: int = 0,
    script: str = '',
    module: str = '__main__',
    config: dict = {},
):
    """Runs a HTTP server that accepts a form for the given config.

  This is a blocking call that doesn't return to the caller.
  """
    if http_port <= 0:
        http_port = _FLAGS.http_port
        if http_port <= 0:
            return False
    global _HTTP_CONFIG
    if not config:
        config = ConfigMap(_FLAGS.http_config).get_configs()
    if http_port:
        config['http_port'] = http_port
    if script:
        config['script'] = script

    # Add form inputs for all flags for the module.
    if not module:
        module = basename(sys.argv[0]).split('.py')[0]
    logging.info(f'Getting flags for module: {module}')
    form_config = _get_form_config(config)
    form_inputs = form_config.get('form_input', [])
    for flag in _FLAGS.get_flags_for_module(module):
        if not flag.name.startswith('http'):
            input_param = dict()
            input_param['name'] = flag.name
            input_param['description'] = flag.help
            input_param['type'] = 'text'
            form_inputs.append(input_param)
    form_config['form_input'] = form_inputs

    logging.info(f'Starting HTTP server with config: {config}')

    # TODO: find a way to pass config to handler.
    _HTTP_CONFIG = dict(config)
    httpd = ThreadedHTTPServer(
        http_port=config.get('http_port', _FLAGS.http_port),
        handler=ProcessHandler,
        num_threads=config.get('http_threads', _FLAGS.http_server_threads),
    )
    httpd.serve_forever(_FLAGS.http_server_timeout)
    return True


def main(_):
    run_http_server()


if __name__ == '__main__':
    app.run(main)
