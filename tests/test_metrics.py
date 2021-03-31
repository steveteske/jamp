import os
import sys
from pprint import pprint
from unittest.mock import patch, MagicMock

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

def build_sprint(name,id):
    mock_sprint = MagicMock()
    mock_sprint.name = name
    mock_sprint.id = id
    return mock_sprint


@pytest.fixture
def mock_sprints():
    mock_sprints = []
    mock_sprints.append(build_sprint("Sprint 1.1", 100))
    mock_sprints.append(build_sprint("Sprint 1.2", 200))
    mock_sprints.append(build_sprint("Sprint 1.3", 300))
    mock_sprints.append(build_sprint("Sprint 1.4", 400))
    return mock_sprints


def build_board(name: str, id: int, type: str) -> MagicMock:
    mock_board = MagicMock()
    mock_board.name = name
    mock_board.id = id
    mock_board.type = type

    return mock_board


@pytest.fixture
def mock_boards():
    mock_boards = []
    mock_boards.append(build_board('JAMP', 100, 'scrum'))
    mock_boards.append(build_board('ABC', 150, 'scrum'))
    mock_boards.append(build_board('XYZ', 200, 'kanban'))

    return mock_boards

@pytest.fixture
def mock_sprint_report():
    mock_sprint_report = MagicMock()
    mock_sprint_report.committed = 17.0
    return mock_sprint_report


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
def test_metrics_required_args_good_password(mock_jira_field_mapper,
                                                  mock_jira_teams,
                                                  mock_jira_reports,
                                                  mock_jira,
                                                  program_metrics,
                                                  mock_server,
                                                  mock_password,
                                                  mock_user,
                                                  mock_boards,
                                                  mock_sprints,
                                             mock_sprint_report):

    # Setup
    mock_jira.return_value.boards.return_value = mock_boards
    mock_jira.return_value.sprints.return_value = mock_sprints

    mock_jira_reports.return_value.sprint_report.return_value = mock_sprint_report

    # Test
    pm = program_metrics(["metrics.py",
                          '--user', mock_user,
                          '--server', mock_server
                          ],
                         password=mock_password)
    pm.build_report()

    # Verification
    assert mock_server == mock_jira.call_args[1]['server']
    assert (mock_user, mock_password) == mock_jira.call_args[1]['basic_auth']

    assert mock_server == mock_jira_reports.call_args[1]['server']
    assert (mock_user, mock_password) == mock_jira_reports.call_args[1]['basic_auth']

    assert mock_jira.return_value.boards.called
    assert mock_jira.return_value.sprints.called
    assert mock_jira.return_value.sprints.call_count == 2 # two scrum boards

    assert not mock_jira_teams.called

    assert mock_jira_field_mapper.called


@patch('metrics.JIRA')
@patch('metrics.JIRAReports')
@patch('metrics.JIRATeams')
@patch('metrics.JiraFieldMapper')
def test_metrics_args_board(mock_jira_field_mapper,
                            mock_jira_teams,
                            mock_jira_reports,
                            mock_jira,
                            program_metrics,
                            mock_server,
                            mock_password,
                            mock_user,
                            mock_boards,
                            mock_sprints,
                            mock_sprint_report):

    mock_jira.return_value.boards.return_value = mock_boards
    mock_jira.return_value.sprints.return_value = mock_sprints

    mock_jira_reports.return_value.sprint_report.return_value = mock_sprint_report

    pm = program_metrics(["metrics.py",
                          '--user', mock_user,
                          '--server', mock_server,
                          '--board', 'JAMP:MATCH_EXACT'
                          ],
                         password=mock_password)

    pm.build_report()

    assert mock_server == mock_jira.call_args[1]['server']
    assert (mock_user, mock_password) == mock_jira.call_args[1]['basic_auth']

    assert mock_jira.return_value.boards.called
    assert mock_jira.return_value.sprints.called
    assert mock_jira.return_value.sprints.call_count == 1

    assert mock_server == mock_jira_reports.call_args[1]['server']
    assert (mock_user, mock_password) == mock_jira_reports.call_args[1]['basic_auth']

    assert not mock_jira_teams.called

    assert mock_jira_field_mapper.called


@patch('metrics.JIRA')
@patch('metrics.JIRAReports')
@patch('metrics.JIRATeams')
@patch('metrics.JiraFieldMapper')
def test_metrics_args_board_no_command(mock_jira_field_mapper,
                                       mock_jira_teams,
                                       mock_jira_reports,
                                       mock_jira,
                                       program_metrics,
                                       mock_server,
                                       mock_password,
                                       mock_user,
                                       mock_boards,
                                       mock_sprints,
                                       mock_sprint_report):

    mock_jira.return_value.boards.return_value = mock_boards
    mock_jira.return_value.sprints.return_value = mock_sprints

    mock_jira_reports.return_value.sprint_report.return_value = mock_sprint_report

    pm = program_metrics(["metrics.py",
                          '--user', mock_user,
                          '--server', mock_server,
                          '--board', 'JAMP'
                          ],
                         password=mock_password)

    pm.build_report()

    assert mock_server == mock_jira.call_args[1]['server']
    assert (mock_user, mock_password) == mock_jira.call_args[1]['basic_auth']

    assert mock_jira.return_value.boards.called
    assert mock_jira.return_value.sprints.called
    assert mock_jira.return_value.sprints.call_count == 1

    assert mock_server == mock_jira_reports.call_args[1]['server']
    assert (mock_user, mock_password) == mock_jira_reports.call_args[1]['basic_auth']

    assert not mock_jira_teams.called

    assert mock_jira_field_mapper.called
