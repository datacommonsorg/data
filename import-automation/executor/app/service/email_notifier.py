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
Class for sending email notifications about import progress.
"""

import smtplib
from typing import List

from app import utils


class EmailNotifier:
    """Class for sending email notifications about import progress.

    Attributes:
        account: Sender email account as a string.
        password: The corresponding password, app password, or access token
            as a string.
    """

    def __init__(self, account: str, password: str):
        self.account = account
        self.password = password

    def send(self, subject: str, body: str,
             receiver_addresses: List[str]) -> None:
        """Sends an email.

        Args:
            subject: Email subject as a string.
            body: Email body as a string.
            receiver_addresses: List of receiver email addresses
                each as a string.

        Raises:
            Same exceptions as smtplib.SMTP_SSL.__init__,
            smtplib.SMTP_SSL.login, smtplib.SMTP_SSL.sendmail.
        """
        with smtplib.SMTP_SSL('smtp.gmail.com') as server:
            server.login(self.account, self.password)
            email = (f'From: {self.account}\n'
                     f'To: {utils.list_to_str(receiver_addresses)}\n'
                     f'Subject: {subject}\n'
                     '\n'
                     f'{body}\n')
            server.sendmail(self.account, receiver_addresses, email)
