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

from frozendict import frozendict

'''
Maturities for which interest rates are provided by BEA.
Treasury bills have maturities of a year or less, notes greater than 1 year up
to 10 years, and bonds greater than 10 years.
'''
MATURITIES = frozendict({
    "1-month": "Bill", "3-month": "Bill", "6-month": "Bill",
    "1-year": "Bill", "2-year": "Note", "3-year": "Note", "5-year": "Note",
    "7-year": "Note", "10-year": "Note", "20-year": "Bond", "30-year": "Bond"
})
