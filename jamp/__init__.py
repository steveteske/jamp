import datetime
from jira import JIRA
from jira.resources import Resource


JIRA_KEY_FIELDS = 'fields'
JIRA_KEY_NAMES = 'name'


def jira_date_str(date: datetime) -> str:
    VELOCITY_PARM_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
    return date.strftime(VELOCITY_PARM_DATE_FORMAT)[:-3] + 'Z'


class JiraFieldMapper:

    def __init__(self, options, session):
        self._options = options
        self._session = session
        self._map = self._build_field_name_map()

    def _build_field_name_map(self):
        # Here's how to get the fields to name mapping from the issues resource...
        # The following is best, but it only shows the create screen types, so if you are looking
        # ..for everything available, use the 'search' mechanism.
        # issue_key = "issue/createmeta?projectKeys=JAMP&expand=projects.issuetypes.fields"
        issue_key = "search?maxResults=1&expand=names"
        resource = Resource(issue_key,
                            options=self._options,
                            session=self._session)

        resource.find(None)  # 'find(None)' loads the resource, but doesn't return anything

        map = {}
        for key, value in resource.raw['names'].items():
            map[value] = key

        return map

    def jira_key(self, name) -> str:
        return self._map[name]

