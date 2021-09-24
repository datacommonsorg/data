# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = ["Thejesh GN (i@thejeshgn.com)"]


class CodeFormatter:

    @staticmethod
    def format_lgd_state_code(s):
        # Converts into two character length code
        # If the value is `0` then it makes it empty
        # If the length is single character then it prepends it
        # with `0` to make it two character length
        s = s.zfill(2)
        return "" if s == "00" else s

    @staticmethod
    def format_lgd_district_code(s):
        # Converts into three character length code
        # If the value is `0` then it makes it empty
        # If the length is less than three characters
        # then it prepends it with `0`s to make it
        # three characters length
        s = s.zfill(3)
        return "" if s == "000" else s

    @staticmethod
    def format_census2011_code(s):
        # Converts into three character length code
        # If the value is `0` then it makes it empty
        # If the length is less than three characters
        # then it prepends it with `0`s to make it
        # three characters length
        s = s.zfill(3)
        return "" if s == "000" else s

    @staticmethod
    def format_census2001_district_code(state_code, district_code):
        # Census 2001 code is a combication of state code
        # And district code seaparated by period (.)
        # Each part is converted into two character length code
        # If the value is `0` then it makes it empty
        # If the length is single character then it prepends it
        # with `0` to make it two character length
        state_code = state_code.zfill(2)
        district_code = district_code.zfill(2)
        if district_code == "00" or state_code == "00":
            return ""
        else:
            return "{state_code}.{district_code}".format(
                state_code=state_code, district_code=district_code)
