"""This script has the tests for wfigs_data.py.
It imports two test datasets and checks if the processed output matches the
expected output.
"""
import unittest
import os
import pandas as pd
import sys
from datetime import datetime

module_dir_ = os.path.dirname(__file__)
sys.path.insert(0, module_dir_)
import wfigs_data


def _GetTestPath(relative_path):
    return os.path.join(module_dir_, relative_path)


def _GetEpochMillis(x):
    if not pd.isna(x):
        utc_time = datetime.strptime(x, "%Y/%m/%d %H:%M:%S")
        return (utc_time - datetime(1970, 1, 1)).total_seconds() * 1000
    return None


def _GetDatetime(x):
    if not pd.isna(x):
        return datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
    return None


class PreprocessDataTest(unittest.TestCase):
    """This class has the method required to test preprocess_data script."""

    def test_ProcessDF(self):
        # expected_df = pd.read_csv(_GetTestPath("test_data/expected_output.csv"))
        historical_df = pd.read_csv(_GetTestPath("test_data/historical.csv"))
        current_df = pd.read_csv(_GetTestPath("test_data/current.csv"))
        expected_df = pd.read_csv(_GetTestPath("test_data/expected.csv"))
        df = pd.concat([current_df, historical_df], ignore_index=True)
        df["FireDiscoveryDateTime"] = df["FireDiscoveryDateTime"].apply(
            _GetEpochMillis)
        df["InitialResponseDateTime"] = df["InitialResponseDateTime"].apply(
            _GetEpochMillis)
        df["ContainmentDateTime"] = df["ContainmentDateTime"].apply(
            _GetEpochMillis)
        df["ControlDateTime"] = df["ControlDateTime"].apply(_GetEpochMillis)
        df["FireCause"] = df["FireCause"].apply(lambda x: None
                                                if pd.isna(x) else x)
        df["FireCauseGeneral"] = df["FireCauseGeneral"].apply(
            lambda x: None if pd.isna(x) else x)
        df["FireCauseSpecific"] = df["FireCauseSpecific"].apply(
            lambda x: None if pd.isna(x) else x)
        processed = wfigs_data.process_df(df)
        expected_df["FireDiscoveryDateTime"] = expected_df[
            "FireDiscoveryDateTime"].apply(_GetDatetime)
        expected_df["InitialResponseDateTime"] = expected_df[
            "InitialResponseDateTime"].apply(_GetDatetime)
        expected_df["ContainmentDateTime"] = expected_df[
            "ContainmentDateTime"].apply(_GetDatetime)
        expected_df["ControlDateTime"] = expected_df["ControlDateTime"].apply(
            _GetDatetime)
        sort_column_list = [
            "dcid", "name", "typeOf", "Location", "FireCause",
            "FireCauseGeneral", "FireCauseSpecific", "FireDiscoveryDateTime",
            "ControlDateTime", "ContainmentDateTime", "BurnedArea", "Costs",
            "TotalIncidentPersonnel", "IrwinID", "wfigsFireID", "ParentFire",
            "InitialResponseDateTime", "InitialResponseAcres"
        ]
        self.assertIsNone(
            pd.testing.assert_frame_equal(
                processed.sort_values(by=sort_column_list, ignore_index=True),
                expected_df.sort_values(by=sort_column_list, ignore_index=True),
                check_dtype=False))


if __name__ == "__main__":
    unittest.main()
