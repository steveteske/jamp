import json
import os

import pytest

dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def mock_sprint_report():
    f = open(os.path.join(dir_path, "test_data/mock_sprintreport.json"))
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