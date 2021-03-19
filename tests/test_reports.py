import pytest

from jamp.reports import ProgramReport, SprintMetrics
from jamp.resources import SprintReport, VelocityReport


def test_sprint_report():
    pr = ProgramReport()

    assert False

@pytest.fixture
def sprint_metrics(mock_options, mock_sprint_report_with_id,mock_velocity_report_with_id ):
    sr = SprintReport(options=mock_options, session=None, raw=mock_sprint_report_with_id)
    vr = VelocityReport(options=mock_options, session=None, raw=mock_velocity_report_with_id)
    return SprintMetrics(2, sr, vr)


def test_sprint_metrics(sprint_metrics):
    actual = sprint_metrics.completion_ratio()
    assert 16/18 == actual


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






