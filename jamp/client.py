from datetime import datetime, timedelta
import pprint

from jira import JIRA
from jira.client import ResultList

from jamp.resources import SprintReport, Team, VelocityReport
from jamp import jira_date_str


class JIRAReports(JIRA):

    def sprint_report(self, board_id, sprint_id) -> SprintReport:
        # ...rest/greenhopper/1.0/rapid/charts/sprintreport?rapidViewId=1&sprintId=1
        parms = f'rapidViewId={board_id}&sprintId={sprint_id}'
        r_json = self._get_json(f'rapid/charts/sprintreport?{parms}',
                                base=self.AGILE_BASE_URL)
        # This is a hack to make the Sprint Report a resource, even if it's not
        # ...really a resource.
        if 'id' not in r_json:
            r_json['board_id'] = board_id
            r_json['sprint_id'] = sprint_id
            r_json['id'] = f'rapidViewId={board_id}&sprintId={sprint_id}'

        sprint_report = SprintReport(options=self._options, session=self._session, raw=r_json)
        return sprint_report

    def velocity_report(self, board_id, finished_before=None, finished_after=None  ):
        """
        sprint_id
        rapidViewId=1&sprintsFinishedBefore=2021-03-03T04%3A59%3A59.999Z&sprintsFinishedAfter=2020-12-02T05%3A00%3A00.000Z&_=1614720709744
        """
        # ...rest/greenhopper/1.0/rapid/charts/sprintreport?rapidViewId=1&sprintId=1

        finish_after_time = datetime.now()
        finish_before_time = finish_after_time - timedelta(days=365)

        finish_after_str = jira_date_str(finish_after_time)
        finish_before_str = jira_date_str(finish_before_time)

        parms = f'rapidViewId={board_id}&sprintsFinishedBefore={finish_after_str}'\
                f'&sprintsFinishedAfter={finish_before_str}'

        r_json = self._get_json(f'rapid/charts/velocity.json?{parms}',
                                base=self.AGILE_BASE_URL)

        r_json['id'] = board_id

        velocity_report = VelocityReport(options=self._options, session=self._session, raw=r_json)

        return velocity_report


class JIRATeams(JIRA):

    def teams(self, startAt=0, maxResults=50, type=None, name=None) -> ResultList:
        r_json = self._get_json('team', base=self.AGILE_BASE_URL)
        teams = [Team(self._options, self._session, raw_teams_json) for raw_teams_json in r_json]
        return ResultList(teams, 0, len(teams), len(teams), True)
