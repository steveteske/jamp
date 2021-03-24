import pprint

from jira.resources import Resource, GreenHopperResource

import jamp
from jamp import JiraFieldMapper


class Team(Resource):

    def __init__(self, options, session, raw=None):
        options['agile_rest_path'] = 'teams-api'
        Resource.__init__(self, 'team/{0}', options, session, raw)
        if raw:
            self._parse_raw(raw)


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
         'issueKeysAddedDuringSprint')
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

        'issueKeysAddedDuringSprint' is a dict of issues keys rather than
        a list of keys.

        :param raw:
        :return:
        """

        # Call the parent method to do the normal processing
        GreenHopperResource._parse_raw(self, raw)

        # Save off the list of added issues
        self._added = raw['contents']['issueKeysAddedDuringSprint']

        self._added_sum = 0
        for issue_key in self._added:
            resource_format = f"issue/{issue_key}"
            resource = self._build_resource(resource_format)

            story_points_field = self.jira_key('Story Points')
            self._added_sum += resource.raw[jamp.JIRA_KEY_FIELDS][story_points_field]

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
            return 0.0
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
                if item == 'issueKeysAddedDuringSprint':
                    return self._added
                else:
                    return getattr(self.contents, item)
            except KeyError as err:
                return super().__getattr__(item)

        if item in COUNTS:
            base_item = item[:-len('Count')]
            if base_item == 'issueKeysAddedDuringSprint':
                return len(self._added)

            value = getattr(self.contents, base_item)

            if value:
                return len(value)
            else:
                return 0

        else:
            return super().__getattr__(item)

    def jira_key(self, field_key):
        return self._map.jira_key(field_key)

    @property
    def added_sum(self):
        return self._added_sum

    @property
    def committed(self):
        committed = self.issuesNotCompletedInitialEstimateSum + \
                    self.completedIssuesInitialEstimateSum - \
                    self.issues_added_initial_estimate_sum

        return committed

    def _initial_estimate_stat(self, issues_list: list, issue_match=None) -> float:
        sum = 0
        for issue in issues_list:
            if 'estimateStatistic' not in issue:
                return 0.0

            stat_field = issue['estimateStatistic']['statFieldValue']
            if stat_field:
                stat = stat_field['value']
            else:
                stat = 0.0

            if issue_match:
                if issue['key'] == issue_match:
                    return stat
            else:
                sum += stat

        return sum

    def _final_estimate_stat(self, issues_list: list, issue_match=None) -> float:
        sum = 0
        for issue in issues_list:
            stat_field = issue['currentEstimateStatistic']['statFieldValue']
            if stat_field:
                stat = stat_field['value']
            else:
                stat = 0.0

            if issue_match:
                if issue['key'] == issue_match:
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
        sum = 0
        for issue_key in self._added:
            contents = self.raw['contents']
            sum += self._initial_estimate_stat(contents['completedIssues'], issue_key)
            sum += self._initial_estimate_stat(contents['issuesNotCompletedInCurrentSprint'], issue_key)
            #'completedIssues'
            #'issuesNotCompletedInCurrenSprint'
            #'puntedIssues'?????
            #'issuesCompletedInAnotherSprint?????

        return sum

class VelocityReport(GreenHopperResource):
    """
    .../rapid/charts/velocity.json?rapidViewId=1&sprintsFinishedBefore=2021-03-03T04%3A59%3A59.999Z&sprintsFinishedAfter=2020-12-02T05%3A00%3A00.000Z&_=1614720709744

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

        committed = stat_entry[stat]['value']
        return float(committed)

    def committed(self, sprint_id: int) -> float:
        return self._velocity_stat(sprint_id, 'estimated')

    def completed(self, sprint_id: int) -> float:
        return self._velocity_stat(sprint_id, 'completed')
