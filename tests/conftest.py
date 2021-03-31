import json
import os
from unittest.mock import patch, MagicMock

import pytest

from jamp import JiraFieldMapper
from jamp.resources import SprintReport

dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def mock_av_boards():
    f = open(os.path.join(dir_path, "test_data/mock_av_boards.json"))
    return json.load(f)


@pytest.fixture
def mock_sprint_report():
    f = open(os.path.join(dir_path, "test_data/mock_sprintreport.json"))
    return json.load(f)


@pytest.fixture
def mock_issue_av14():
    f = open(os.path.join(dir_path, "test_data/mock_issue_av14.json"))
    return json.load(f)


@pytest.fixture
def mock_issue_av16():
    f = open(os.path.join(dir_path, "test_data/mock_issue_av16.json"))
    return json.load(f)


@pytest.fixture
def mock_sprint_report_with_id(mock_sprint_report):
    r_json = mock_sprint_report.copy()
    r_json['id'] = 'fake'
    return r_json


@pytest.fixture
def mock_velocity_report():
    f = open(os.path.join(dir_path, "test_data/mock_velocityreport.json"))
    return json.load(f)


@pytest.fixture
def mock_velocity_report_with_id(mock_velocity_report):
    r_json = mock_velocity_report.copy()
    r_json['id'] = 'fake'
    return r_json


@pytest.fixture
def mock_options():
    return {'agile_rest_path': None,
            'server': 'localhost',
            'agile_rest_api_version': '2',
            }


@pytest.fixture
@patch.object(SprintReport, '_build_resource')
@patch.object(JiraFieldMapper, '_build_field_name_map')
@patch.object(JiraFieldMapper, 'jira_key')
def sprint_report(mock_jira_key, mock_field_mapper, mock_field_mapper_build_map,
                  mock_options, mock_sprint_report_with_id, mock_velocity_report_with_id,
                  mock_issue_av14, mock_issue_av16):

    resource_mock14 = MagicMock()
    resource_mock14.raw = mock_issue_av14

    resource_mock16 = MagicMock()
    resource_mock16.raw = mock_issue_av16

    mock_field_mapper_build_map.side_effect = [resource_mock14, resource_mock16]

    mock_jira_key.return_value = 'customfield_10111'
    sr = SprintReport(options=mock_options, session=None, raw=mock_sprint_report_with_id)
    return sr