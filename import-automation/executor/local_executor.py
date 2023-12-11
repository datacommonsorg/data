# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Local import executor. Run '. run_local_executor.sh --help' for usage.

The local executor downloads the main branch of a repository and produces
the data files of an import specified by its absolute import name of the form
<path to the directory containing the manifest>:<import name>.

username and access_token are used for authentication with GitHub to access
private repositories and get higher rate limits. They need to be both absent or
provided. See
https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token
for how to create access tokens.

owner_username and repo_name uniquely identify a repository. E.g., in
'https://github.com/datacommonsorg/data', 'datacommonsorg' is the owner_username
and 'data' is the repo_name.
"""

import os

from absl import flags
from absl import app

from app import configs
from app.executor import import_target
from app.executor import import_executor
from app.service import file_uploader
from app.service import github_api

_IMPORT_NAME_FORM = '''
<path to the directory containing the manifest>:<import name>
'''.strip()

FLAGS = flags.FLAGS
flags.DEFINE_string(
    name='import_name',
    default=None,
    help=('Absolute import name of the import to execute of the form '
          f'{_IMPORT_NAME_FORM}.'),
    short_name='i')
flags.DEFINE_string(name='output_dir',
                    default='.',
                    help='Path to the output directory.',
                    short_name='o')
flags.DEFINE_string(name='repo_name',
                    default='data',
                    help='Name of the GitHub repository containing the import.',
                    short_name='r')
flags.DEFINE_string(
    name='owner_username',
    default='datacommonsorg',
    help=('GitHub username of the owner of the GitHub repository '
          'containing the import.'),
    short_name='u')
flags.DEFINE_string(name='username',
                    default='',
                    help='GitHub username for authentication.',
                    short_name='n')
flags.DEFINE_string(name='access_token',
                    default='',
                    help='GitHub access token for authentication.',
                    short_name='t')

flags.mark_flag_as_required('import_name')
flags.register_validator('import_name',
                         import_target.is_absolute_import_name,
                         message=('--import_name must be of the form '
                                  f'{_IMPORT_NAME_FORM}.'))


def main(_):
    """Runs the local executor."""
    config = configs.ExecutorConfig(
        github_repo_name=FLAGS.repo_name,
        github_repo_owner_username=FLAGS.owner_username,
        github_auth_username=FLAGS.username,
        github_auth_access_token=FLAGS.access_token,
        user_script_env=os.environ)
    executor = import_executor.ImportExecutor(
        uploader=file_uploader.LocalFileUploader(output_dir=FLAGS.output_dir),
        github=github_api.GitHubRepoAPI(config.github_repo_owner_username,
                                        config.github_repo_name),
        config=config)
    results = executor.execute_imports_on_update(FLAGS.import_name)
    print(results)


if __name__ == '__main__':
    app.run(main)
