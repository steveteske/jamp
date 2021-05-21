from datetime import datetime, timedelta
import pprint

from jira import JIRA
from jira.client import ResultList

from jamp.resources import SprintReport, Team, VelocityReport, CfdReport
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
         ...rest/greenhopper/1.0/rapid/charts/sprintreport?
            rapidViewId=1&
            sprintId=1
            sprintsFinishedBefore=2021-03-03T04%3A59%3A59.999Z&
            sprintsFinishedAfter=2020-12-02T05%3A00%3A00.000Z&_=1614720709744
        """

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

    def cfd_report(self, board_id, finished_before=None, finished_after=None  ):
        """
    1) https://ale-dev.atlassian.net/rest/greenhopper/1.0/xboard/config.json?
            returnDefaultBoard=false&
            rapidViewId=1

    2) https://ale-dev.atlassian.net/rest/greenhopper/1.0/rapid/charts/cumulativeflowdiagram?
            rapidViewId=1&
            swimlaneId=1&
            columnId=4&
            columnId=5&
            columnId=6
        """

        parms = f'returnDefaultBoard=false&' \
                f'rapidViewId={board_id}&'

        config = self._get_json(f'xboard/config.json?{parms}',
                                base=self.AGILE_BASE_URL)

        swimlane_parm = ""
        for swimlane in config['currentViewConfig']['swimlanes']:
            swimlane_parm += f"&swimlaneId={swimlane['id']}"

        col_parm = ""
        for col in config['currentViewConfig']['columns']:
            col_parm += f"&columnId={col['id']}"

        parms = f"rapidViewId={board_id}{swimlane_parm}{col_parm}"

        r_json = self._get_json(f'rapid/charts/cumulativeflowdiagram?{parms}',
                                base=self.AGILE_BASE_URL)

        r_json['id'] = board_id

        cfd_report = CfdReport(options=self._options,
                               session=self._session,
                               raw=r_json,
                               config=config)

        return cfd_report


class JIRATeams(JIRA):

    def teams(self, startAt=0, maxResults=50, type=None, name=None) -> ResultList:
        r_json = self._get_json('team', base=self.AGILE_BASE_URL)
        teams = [Team(self._options, self._session, raw_teams_json) for raw_teams_json in r_json]
        return ResultList(teams, 0, len(teams), len(teams), True)
