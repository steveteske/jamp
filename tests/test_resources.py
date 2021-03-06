import math

from jamp import NAN
from jamp.resources import SprintReport, COUNTS, STATS, LISTS, VelocityReport
import pytest


values = (3, 3, 1, 0, 2,  # counts

          6.0, 6.0, 17.0, 8.0, 8.0,
          NAN, 8.0, NAN, NAN,  # stats

          ["AV-15", "AV-16", "AV-17"],
          ["AV-10", "AV-13", "AV-14"],
          ['AV-13000'],
          [],
          {'AV-14': True, 'AV-16': True}, 'TheEnd')  # lists

parms = [[x, values[i]] for i, x in enumerate(COUNTS + list(STATS) + list(LISTS))]


@pytest.mark.parametrize("test_input,expected", parms)
def test_sprint_report(mock_sprint_report_with_id, mock_options, test_input, expected, sprint_report):
    # sr = SprintReport(options=mock_options, session=None, raw=mock_sprint_report_with_id)
    sr = sprint_report
    value = getattr(sr, test_input)

    if isinstance(value, list):
        # Test for list types
        for i, v in enumerate(value):
            assert v.key == expected[i]
    elif isinstance(value, float) and math.isnan(expected):
        # Test for all other NaN expected values
        assert math.isnan(value)
    else:
        # Test for everything else
        assert value == expected


velocity_parms = \
    [["sprints", ['Sample Sprint 2', 'Sample Sprint 1']],
     ["velocityStatEntries", [{'id': "2", 'estimated': 18.0, 'completed': 16.0},
                              {'id': "1", 'estimated': 11.0, 'completed': 11.0}]
     ]
    ]


@pytest.mark.parametrize("test_input,expected", velocity_parms)
def test_velocity_report(mock_velocity_report_with_id, mock_options, test_input, expected):
    sr = VelocityReport(options=mock_options, session=None, raw=mock_velocity_report_with_id)

    value = getattr(sr, test_input)

    if isinstance(value, list):
        # Test for list types
        for i, v in enumerate(value):
            assert v.name == expected[i]
    else:
        # Test for everything else
        for e in expected:
            sprint = getattr(value, e['id'])
            assert sprint.estimated.value == e['estimated']
            assert sprint.completed.value == e['completed']


def test_sprint_1_report_committed(sprint_1_report):
    assert 39.0 == sprint_1_report.committed


def test_sprint_2_report_committed(sprint_2_report):
    assert 35.0 == sprint_2_report.committed


def test_sprint_6_report_committed(sprint_6_report):
    assert 68.0 == sprint_6_report.committed

