import datetime
import math
import pprint
import numpy as np
import pandas as pd
from jira.resources import Resource, GreenHopperResource

import jamp
from jamp import JiraFieldMapper, NAN, JIRA_KEY_KEY, JIRA_KEY_VALUE


class Team(Resource):

    def __init__(self, options, session, raw=None):
        options['agile_rest_path'] = 'teams-api'
        Resource.__init__(self, 'team/{0}', options, session, raw)
        if raw:
            self._parse_raw(raw)

KEY_ISSUE_KEYS_ADDED_DURING_SPRINT = 'issueKeysAddedDuringSprint'
KEY_ESTIMATE_STATISTIC = 'estimateStatistic'

STATS = ('completedIssuesInitialEstimateSum',
         'completedIssuesEstimateSum',
         'allIssuesEstimateSum',
         'issuesNotCompletedInitialEstimateSum',
         'issuesNotCompletedEstimateSum',
         'puntedIssuesInitialEstimateSum',
         'puntedIssuesEstimateSum',
         'issuesCompletedInAnotherSprintInitialEstimateSum',
         'issuesCompletedInAnotherSprintEstimateSum')
LISTS = ('completedIssues',
         'issuesNotCompletedInCurrentSprint',
         'puntedIssues',
         'issuesCompletedInAnotherSprint',
         KEY_ISSUE_KEYS_ADDED_DURING_SPRINT)
COUNTS = [x + 'Count' for x in LISTS]


class SprintReport(GreenHopperResource):
    """A SprintReport."""

    def __init__(self, options, session, raw=None):
        self._map = JiraFieldMapper(options, session)
        options['agile_rest_path'] = 'greenhopper'
        path = 'rapid/charts/sprintreport?{0}'
        GreenHopperResource.__init__(self, path, options, session, raw)

    def _parse_raw(self, raw):
        """
        Overridden to address a single attribute that doesn't match how other Resources
        define attributes:

        KEY_ISSUE_KEYS_ADDED_DURING_SPRINT is a dict of issues keys rather than
        a list of keys.

        :param raw:
        :return:
        """

        # Call the parent method to do the normal processing
        GreenHopperResource._parse_raw(self, raw)

        # Save off the list of added issues
        self._added = raw['contents'][KEY_ISSUE_KEYS_ADDED_DURING_SPRINT]

        self._added_sum = 0
        for issue_key in self._added:
            resource_format = f"issue/{issue_key}"
            resource = self._build_resource(resource_format)

            story_points_field = self.jira_key('Story Points')
            story_point = resource.raw[jamp.JIRA_KEY_FIELDS][story_points_field]

            # sometime story_points returns NoneType so check it first
            if story_point:
                self._added_sum += story_point

    def _build_resource(self, resource_format):
        resource = Resource(resource_format,
                            options=self._options,
                            session=self._session)
        resource.find(None)  # Simply calling find() populates the Resource
        return resource

    def delete(self, params=None):
        raise NotImplementedError('JIRA Agile Public API does not support SprintReport removal')

    def _normalize_contents_stat(self, stat):
        """
        Sprint Report contents come in two flavors:
        1) Stats
        2) Lists

        For the stats, they have the following format:
        { <stat_name> : { text: <text_value>,
                        { value: <float_value> }
        }

        But, if the value is not defined, the 'text' will be "null" and
        the 'value' entry will be absent.

        This method solves that problem of getting undefined property when 'text == "null"

        :param stat: This is the PropertyHolder key representing parent structure
        :return: float value of the stats or 0.0 if 'null'.
        """
        if stat.text == 'null':
            return NAN
        else:
            return stat.value

    def __getattr__(self, item):
        """
        This overridden __getattr__ method allows direct access the json dict elements.

        This methods flattens the hierarchy so there is direct access to stats rather than having to
        dereference through "contents" (i.e. 'contents' : { '...Sum' { 'text': '2', 'value': 2.0 }}} )

        If the attribute is not found locally, call the parent to utilize the super class
        __getattr__.

        :param item: attribute name requested by the caller
        :return: Any
        """

        if item in STATS:
            try:
                return self._normalize_contents_stat(getattr(self.contents, item))
            except KeyError as err:
                return super().__getattr__(item)

        if item in LISTS:
            try:
                if item == KEY_ISSUE_KEYS_ADDED_DURING_SPRINT:
                    return self._added
                else:
                    return getattr(self.contents, item)
            except KeyError as err:
                return super().__getattr__(item)

        if item in COUNTS:
            base_item = item[:-len('Count')]
            if base_item == KEY_ISSUE_KEYS_ADDED_DURING_SPRINT:
                return len(self._added)

            value = getattr(self.contents, base_item)

            if value:
                return len(value)
            else:
                return 0

        else:
            return super().__getattribute__(item)

    def jira_key(self, field_key) -> str:
        return self._map.jira_key(field_key)

    @property
    def added_sum(self) -> float:
        return self._added_sum

    @property
    def added_count(self) -> float:
        return len(self._added)

    @property
    def committed(self) -> float:
        committed = 0.0
        if not math.isnan(self.issuesNotCompletedInitialEstimateSum):
            committed = self.issuesNotCompletedInitialEstimateSum
        if not math.isnan(self.completedIssuesInitialEstimateSum):
            committed += self.completedIssuesInitialEstimateSum
        if not math.isnan(self.puntedIssuesInitialEstimateSum):
            committed += self.puntedIssuesInitialEstimateSum

        committed -= self.issues_added_initial_estimate_sum

        return committed

    @property
    def committed_count(self) -> int:
        committed = 0
        committed += self.issuesNotCompletedInCurrentSprintCount
        committed += self.completedIssuesCount
        committed += self.puntedIssuesCount
        committed -= self.added_count

        return committed

    @property
    def completed_count(self) -> int:
        return self.completedIssuesCount

    @property
    def percent_complete_count(self) -> float:
        if self.committed_count == 0:
            return NAN

        percent_completed = self.completed_count / self.committed_count
        return percent_completed

    def _initial_estimate_stat(self, issues_list: list, issue_match=None) -> float:
        sum = 0
        for issue in issues_list:
            if KEY_ESTIMATE_STATISTIC not in issue:
                return 0.0

            stat_field = issue[KEY_ESTIMATE_STATISTIC]['statFieldValue']
            if stat_field:
                stat = stat_field[JIRA_KEY_VALUE]
            else:
                stat = 0.0

            if issue_match:
                if issue[JIRA_KEY_KEY] == issue_match:
                    return stat
            else:
                sum += stat

        return sum

    def _final_estimate_stat(self, issues_list: list, issue_match=None) -> float:
        sum = 0
        for issue in issues_list:
            stat_field = issue['currentEstimateStatistic']['statFieldValue']
            if stat_field:
                stat = stat_field[JIRA_KEY_VALUE]
            else:
                stat = 0.0

            if issue_match:
                if issue[JIRA_KEY_KEY] == issue_match:
                    return stat
            else:
                sum += stat

        return sum

    @property
    def issues_added_initial_estimate_sum(self):
        """
        Added issues estimates are baked into all the lists for the
        sprint report.
        :return:
        """
        sum = 0.0
        for issue_key in self._added:
            contents = self.raw['contents']
            sum += self._initial_estimate_stat(contents['completedIssues'], issue_key)
            sum += self._initial_estimate_stat(contents['issuesNotCompletedInCurrentSprint'], issue_key)
            sum += self._initial_estimate_stat(contents['puntedIssues'], issue_key)
            # TODO: should this be included: 'issuesCompletedInAnotherSprint?????

        return sum


class VelocityReport(GreenHopperResource):
    """
    .../rapid/charts/velocity.json?
            rapidViewId=1&
            sprintsFinishedBefore=2021-03-03T04%3A59%3A59.999Z&
            sprintsFinishedAfter=2020-12-02T05%3A00%3A00.000Z&_=1614720709744

    """

    def __init__(self, options, session, raw=None):
        options['agile_rest_path'] = 'greenhopper'
        path = 'rapid/charts/velocity.json?{0}'
        GreenHopperResource.__init__(self, path, options, session, raw)

    def _velocity_stat(self, sprint_id, stat):
        try:
            stat_entry = self.raw['velocityStatEntries'][str(sprint_id)]
        except KeyError as e:
            return float('NaN')

        committed = stat_entry[stat][JIRA_KEY_VALUE]
        return float(committed)

    def committed(self, sprint_id: int) -> float:
        return self._velocity_stat(sprint_id, 'estimated')

    def completed(self, sprint_id: int) -> float:
        return self._velocity_stat(sprint_id, 'completed')


class CfdReport(GreenHopperResource):
    """

    """

    def __init__(self, options, session, raw=None, config=None):
        options['agile_rest_path'] = 'greenhopper'
        path = 'rapid/charts/cumulativeflowdiagram?{0}'
        self._config = config
        GreenHopperResource.__init__(self, path, options, session, raw)

    @property
    def board_name(self) -> str:
        return self._config['currentViewConfig']['name']

    def report(self) -> pd.DataFrame:
        KEY_COLUMN_CHANGES = 'columnChanges'
        KEY_COLUMNS = 'columns'
        KEY_COLUMN_FROM = 'columnFrom'
        KEY_COLUMN_TO = 'columnTo'
        KEY_STATUS_TO = 'statusTo'
        KEY_CUM_WIP = 'cumWip'
        KEY_DATE = 'date'

        COL_UNKNOWN = -1

        cum = {}
        _entry = {}
        _exit = {}
        columns = self.raw[KEY_COLUMNS]
        for index, title in enumerate(columns):
            cum[index] = {'title': title['name'],
                          'value': 0
                          }
            _entry[index] = 0
            _exit[index] = 0

        data = []
        for col_key, value in self.raw[KEY_COLUMN_CHANGES].items():
            # print(col_key)
            timestamp = int(col_key)
            ts = datetime.datetime.utcfromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')

            for i in value:
                col_from = i.get(KEY_COLUMN_FROM, COL_UNKNOWN)
                col_to = i.get(KEY_COLUMN_TO, COL_UNKNOWN)
                status_to = i.get(KEY_STATUS_TO, COL_UNKNOWN)

                if col_from != COL_UNKNOWN:
                    _exit[col_from] += 1

                if col_to != COL_UNKNOWN:
                    _entry[col_to] += 1

                for index, col in enumerate(columns):
                    cum[index]['value'] = _entry[index] - _exit[index]

                if status_to in ("4", "10000"):
                    count_open = 1
                else:
                    count_open = 0

                if status_to in ("5", "3"):
                    count_wip = 1
                else:
                    count_wip = 0

                if status_to in ("6", "10001"):
                    count_done = 1
                else:
                    count_done = 0

                item = {
                    'date': ts,
                    'key': i['key'],
                    'from': col_from,
                    'to': col_to,
                    'status_to': status_to,
                    # 'cumEnterOpen': cum_enter_open,
                    # 'cumExitOpen': cum_exit_open,
                    # 'cumEnterInProgress': cum_enter_inprogress,
                    # 'cumExitInProgress' : cum_exit_inprogress,
                    # 'cumEnterFinished': cum_enter_finished,
                    # 'cumExitFinished' : cum_exit_finished,
                    # 'cumEnterDone' : cum_enter_done,
                    # 'cumExitDone' : cum_exit_done,
                    # 'cumWip' : cum_finished + cum_in_progress,
                    # 'countOpen' : count_open,
                    # 'countWip': count_wip,
                    # 'countDone': count_done
                }
                for key, counter in cum.items():
                    item[counter['title']] = counter['value']

                data.append(item)

        df = pd.DataFrame(data)
        if data:
            df = df.astype(dtype={'date': np.datetime64})

        return pd.DataFrame(df)
