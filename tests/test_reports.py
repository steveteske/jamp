from unittest.mock import patch, MagicMock

import pytest

from jamp import JiraFieldMapper
from jamp.reports import SprintMetrics
from jamp.resources import SprintReport, VelocityReport


@pytest.fixture
def sprint_metrics(sprint_report, mock_velocity_report_with_id, mock_options):
    vr = VelocityReport(options=mock_options, session=None, raw=mock_velocity_report_with_id)
    return SprintMetrics(2, sprint_report, vr)


def test_sprint_metrics(sprint_metrics):
    actual = sprint_metrics.completion_ratio()
    assert 16 / 18 == actual


def test_sprint_metrics_committed(sprint_metrics):
    actual = sprint_metrics.velocity_estimated
    assert 18.0 == actual


def test_sprint_metrics_completed(sprint_metrics):
    actual = sprint_metrics.velocity_completed
    assert 16.0 == actual


def test_sprint_metrics_added_sum(sprint_metrics):
    actual = sprint_metrics.added_sum
    assert 6.0 == actual


def test_sprint_metrics_removed_sum(sprint_metrics):
    actual = sprint_metrics.punted_sum
    assert 8.0 == actual


def test_sprint_report(sprint_report):
    assert sprint_report


def test_sprint_report_committed(sprint_report):
    assert 12.0 == sprint_report.committed


def test_sprint_report_added_count(sprint_report):
    assert 2 == sprint_report.added_count


def test_sprint_report_committed_count(sprint_report):
    assert 5 == sprint_report.committed_count


@pytest.fixture
# def sprint_2_metrics(sprint_2_report, mock_velocity_av_report_json, mock_options):
def sprint_2_metrics(sprint_2_report, mock_velocity_report_with_id, mock_options):
    vr = VelocityReport(options=mock_options, session=None, raw=mock_velocity_report_with_id)
    return SprintMetrics(2, sprint_2_report, vr)


