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

    def jira_key(self, field_key):
        return self._map.jira_key(field_key)

    def _parse_raw(self, raw):
        """
        Overriden to address a single attribute that doesn't match how other Resources
        define attributes:

        'issueKeysAddedDuringSprint' is a dict of issues keys rather than
        a list of keys.

        :param raw:
        :return:
        """
        self._added = raw['contents']['issueKeysAddedDuringSprint']
        Resource._parse_raw(self, raw)

        self._added_sum = 0
        for issue_key in self._added:
            resource_format = f"issue/{issue_key}"
            resource = Resource(resource_format,
                                options=self._options,
                                session=self._session)
            resource.find(None)  # Simply calling find() populates the Resource
            story_points_field = self.jira_key('Story Points')

            pprint.pprint(resource.fields)
            self._added_sum += resource.raw[jamp.JIRA_KEY_FIELDS][story_points_field]

    @property
    def added_sum(self):
        return self._added_sum

    def delete(self, params=None):
        raise NotImplementedError('JIRA Agile Public API does not support SprintReport removal')

    def normalize_contents_stat(self, stat):
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
        :return: float value of the stats or NAN if undefined.
        """
        if stat.text == 'null':
            return float("NaN")
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
                return self.normalize_contents_stat(getattr(self.contents, item))
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


class VelocityReport(GreenHopperResource):
    """
    .../rapid/charts/velocity.json?rapidViewId=1&sprintsFinishedBefore=2021-03-03T04%3A59%3A59.999Z&sprintsFinishedAfter=2020-12-02T05%3A00%3A00.000Z&_=1614720709744

    """
    def __init__(self, options, session, raw=None):
        options['agile_rest_path'] = 'greenhopper'
        path = 'rapid/charts/velocity.json?{0}'
        GreenHopperResource.__init__(self, path, options, session, raw)