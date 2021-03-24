import os
import sys
from pprint import pprint
from unittest.mock import patch

import pytest

from jamp import JIRA_PASSWORD_ENV
from metrics import JiraProgramMetrics


@pytest.fixture
def mock_server():
    return 'http://dog.atlassian.com'


@pytest.fixture
def mock_password():
    return '#$#FASF#2340asdf'


@pytest.fixture
def mock_user():
    return 'steve'


@pytest.fixture
def program_metrics(capfd):
    def _program_metrics(args, exception=None, password=None):
        with patch.object(sys, 'argv', args):
            if password:
                os.environ[JIRA_PASSWORD_ENV] = password
            if exception:
                with pytest.raises(exception) as except_info:
                    JiraProgramMetrics()
            else:
                return JiraProgramMetrics()

        out, err = capfd.readouterr()
        return except_info, out, err

    return _program_metrics


def test_metrics_args_no_args(program_metrics):
    info, out, err = program_metrics(["metrics.py"], exception=SystemExit)
    assert 'required: --user, --server' in err
    assert 2 == info.value.code


def test_metrics_args_user_only(program_metrics):
    info, out, err = program_metrics(["metrics.py",
                                      "--user", "steveteske"],
                                     exception=SystemExit)
    assert 'required: --server' in err
    assert 2 == info.value.code


def test_metrics_args_server_only(program_metrics):
    info, out, err = program_metrics(["metrics.py",
                                      "--server", "http://dog.atlassian.com"],
                                     exception=SystemExit)
    assert 'required: --user' in err
    assert 2 == info.value.code


def test_metrics_args_required_args_no_password(program_metrics):
    info, out, err = program_metrics(["metrics.py",
                                      '--user', 'steve',
                                      '--server', 'https://dog.atlassian'
                                      ],
                                     exception=KeyError)

    assert "The environment variable 'JIRA_PASSWORD' is required" in str(info.value)


@patch('metrics.JIRA')
@patch('metrics.JIRAReports')
@patch('metrics.JIRATeams')
@patch('metrics.JiraFieldMapper')
def test_metrics_args_required_args_good_password(mock_jira_field_mapper,
                                                  mock_jira_teams,
                                                  mock_jira_reports,
                                                  mock_jira,
                                                  program_metrics,
                                                  mock_server,
                                                  mock_password,
                                                  mock_user):
    pm = program_metrics(["metrics.py",
                          '--user', mock_user,
                          '--server', mock_server
                          ],
                         password=mock_password)

    assert mock_server == mock_jira.call_args[1]['server']
    assert (mock_user, mock_password) == mock_jira.call_args[1]['basic_auth']

    assert mock_server == mock_jira_reports.call_args[1]['server']
    assert (mock_user, mock_password) == mock_jira_reports.call_args[1]['basic_auth']

    assert not mock_jira_teams.called

    assert mock_jira_field_mapper.called
