# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests the load_bigquery_datasets_pipeline."""

from MySQLdb import MySQLError

from google.apputils import basetest
import mock

# pylint: disable=line-too-long
from google.cloud.security.common.data_access import dao
from google.cloud.security.common.data_access import project_dao
from google.cloud.security.common.data_access import errors as data_access_errors
from google.cloud.security.common.gcp_api import bigquery as bq
from google.cloud.security.common.gcp_api import errors as api_errors
from google.cloud.security.inventory import errors as inventory_errors
from google.cloud.security.inventory.pipelines import load_bigquery_datasets_pipeline
from google.cloud.security.inventory import util as inventory_util
from tests.inventory.pipelines.test_data import fake_bigquery_datasets as fbq
from tests.inventory.pipelines.test_data import fake_configs


class LoadBigQueryDatasetsPipelineTest(basetest.TestCase):
    """Tests for the load_bigquery_datasets_pipeline."""

    def setUp(self):
        """Set up."""

        self.RESOURCE_NAME = 'bigquery'
        self.cycle_timestamp = '20001225T120000Z'
        self.configs = fake_configs.FAKE_CONFIGS
        self.mock_bigquery_client = mock.create_autospec(bq.BigQueryClient)
        self.mock_dao = mock.create_autospec(project_dao.ProjectDao)
        self.pipeline = (
            load_bigquery_datasets_pipeline.LoadBigQueryDatasetsPipeline(
                self.cycle_timestamp,
                self.configs,
                self.mock_bigquery_client,
                self.mock_dao))

    def test_get_project_ids_from_dao_raises(self):
        self.mock_dao.retrieve_project_ids.side_effect = MySQLError

        with self.assertRaises(inventory_errors.LoadDataPipelineError):
            self.pipeline._get_project_ids_from_dao()

    def test_get_project_ids_from_dao_returns(self):
        mock_project_ids = ['1', '2', '3']
        self.mock_dao.retrieve_project_ids.return_value = mock_project_ids

        return_value = self.pipeline._get_project_ids_from_dao()

        self.assertListEqual(mock_project_ids, return_value)
        self.mock_dao.retrieve_project_ids.assert_called_once_with(
            self.RESOURCE_NAME, self.cycle_timestamp)

    def test_get_dataset_by_projectid_raises(self):
        self.pipeline.api_client.retrieve_datasets_for_projectid.side_effect = (
            api_errors.ApiExecutionError('', mock.MagicMock()))

        with self.assertRaises(inventory_errors.LoadDataPipelineError):
            self.pipeline._get_dataset_by_projectid('1')

    def test_get_dataset_by_project_id(self):
        self.pipeline.api_client.retrieve_datasets_for_projectid.return_value = (
            fbq.FAKE_BIGQUERY_DATASET_PROJECT_MAP)

        return_value = self.pipeline._get_dataset_by_projectid('1')

        self.assertListEqual(
            fbq.FAKE_BIGQUERY_DATASET_PROJECT_MAP,
            return_value)

    def test_get_dataset_access_raises(self):
        self.pipeline.api_client.retrieve_dataset_access.side_effect = (
            api_errors.ApiExecutionError('', mock.MagicMock())
        )

        with self.assertRaises(inventory_errors.LoadDataPipelineError):
            self.pipeline._get_dataset_access('1', '2')

    def test_get_dataset_access(self):
        self.pipeline.api_client.retrieve_dataset_access.return_value = (
            fbq.FAKE_DATASET_ACCESS
        )

        return_value = self.pipeline._get_dataset_access('1', '2')

        self.assertListEqual(
            fbq.FAKE_DATASET_ACCESS,
            return_value)

    def test_get_dataset_project_map_raises(self):
        self.pipeline.api_client.retrieve_datasets_for_projectid.side_effect = (
            api_errors.ApiExecutionError('', mock.MagicMock())
        )

        with self.assertRaises(inventory_errors.LoadDataPipelineError):
            self.pipeline._get_dataset_project_map([''])

    def test_get_dataset_project_map(self):
        self.pipeline.api_client.retrieve_datasets_for_projectid.return_value = (
            fbq.FAKE_BIGQUERY_DATASET_PROJECT_MAP)

        return_value = self.pipeline._get_dataset_project_map(
              [fbq.FAKE_BIGQUERY_PROJECTID])

        self.assertListEqual(
            [fbq.FAKE_BIGQUERY_DATASET_PROJECT_MAP],
            return_value)

    @mock.patch.object(
        load_bigquery_datasets_pipeline.LoadBigQueryDatasetsPipeline,
        '_get_dataset_access' )
    def test_get_dataset_access_map(self, mock_dataset_access):
        mock_dataset_access.return_value = (
            fbq.FAKE_DATASET_ACCESS)

        return_value = self.pipeline._get_dataset_access_map(
            fbq.FAKE_BIGQUERY_DATASET_PROJECT_MAP)

        self.assertListEqual(
            fbq.FAKE_DATASET_PROJECT_ACCESS_MAP,
            return_value)

    def test_transform(self):
        self.maxDiff = None
        return_values = []

        for v in self.pipeline._transform(
            fbq.FAKE_DATASET_PROJECT_ACCESS_MAP):
            return_values.append(v)

        self.assertListEqual(
            fbq.FAKE_EXPECTED_LOADABLE_DATASETS,
            return_values)

    @mock.patch.object(
        load_bigquery_datasets_pipeline.LoadBigQueryDatasetsPipeline,
        '_get_loaded_count')
    @mock.patch.object(
        load_bigquery_datasets_pipeline.LoadBigQueryDatasetsPipeline,
        '_load')    
    @mock.patch.object(
        load_bigquery_datasets_pipeline.LoadBigQueryDatasetsPipeline,
        '_transform')
    @mock.patch.object(
        load_bigquery_datasets_pipeline.LoadBigQueryDatasetsPipeline,
        '_retrieve')
    def test_subroutines_are_called_by_run(self, mock_retrieve, mock_transform,
            mock_load, mock_get_loaded_count):
        """Test that the subroutines are called by run."""

        mock_retrieve.return_value = fbq.FAKE_DATASET_PROJECT_ACCESS_MAP
        mock_transform.return_value = fbq.FAKE_EXPECTED_LOADABLE_DATASETS
        self.pipeline.run()

        mock_retrieve.assert_called_once_with()

        mock_transform.assert_called_once_with(
            fbq.FAKE_DATASET_PROJECT_ACCESS_MAP)

        mock_load.assert_called_once_with(
            self.pipeline.RESOURCE_NAME,
            fbq.FAKE_EXPECTED_LOADABLE_DATASETS)

        mock_get_loaded_count.assert_called_once