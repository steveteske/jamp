import pandas as pd
from jira import JIRA
import pprint
import argparse
import os

from jamp import JiraFieldMapper
from jamp.client import JIRAReports, JIRATeams


class JiraProgramMetrics:

    def __init__(self):
        self._args = self.parse_args()
        self._credential = os.environ['JIRA_PASSWORD']
        self._server = self._args.server

        # JIRA for all normal Jira activity (Boards, Sprints, Issues, etc.)
        self.j = JIRA(server=self._server,
                      basic_auth=(self._args.user, self._credential),
                      options={
                          'agile_rest_path': 'agile'
                      })

        # JIRA_Reports used only for reporting, not for general Jira access
        self.jr = JIRAReports(server=self._server,
                              basic_auth=(self._args.user, self._credential))
        if self.use_teams:
            # JIRA for all normal Jira activity (Boards, Sprints, Issues, etc.)
            self.jt = JIRATeams(server=self._server,
                                  basic_auth=(self._args.user, self._credential),
                                  options={
                                       'agile_rest_path': 'teams-api'
                                   })

        self._map = JiraFieldMapper(self.j._options, self.j._session)

    def jira_key(self, field_key):
        return self._map.jira_key(field_key)

    @property
    def use_teams(self):
        return self._args.teams

    def build_report(self) -> pd.DataFrame:
        HEADERS = ("Team", "Sprint", "Added", "Removed", "Not Completed", "Completed", "% Complete")
        board_list = self.j.boards()
        data = []
        for board in board_list:
            for sprint in self.j.sprints(board_id=board.id):
                print(board.id, sprint.id)
                sr = self.jr.sprint_report(board_id=board.id, sprint_id=sprint.id)
                vr = self.jr.velocity_report(board_id=board.id)
                value = sr.completedIssuesInitialEstimateSum
                print(value)
                committed = sr.issuesNotCompletedInitialEstimateSum + \
                    sr.completedIssuesInitialEstimateSum
                percent_complete = sr.completedIssuesEstimateSum / committed

                data.append((board.name,
                             sr.sprint.name,
                             sr.added_sum,
                             sr.puntedIssuesEstimateSum,
                             sr.issuesNotCompletedEstimateSum,
                             sr.completedIssuesEstimateSum,
                             percent_complete
                             ))

        df = pd.DataFrame.from_records(data, columns=HEADERS)
        return df

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Build Program in Jira')
        # group = parser.add_mutually_exclusive_group()
        parser.add_argument('--user', required=True, help='User name')
        parser.add_argument('--server', type=str, help='Jira server address (e.g. http://localhost:8080')
        parser.add_argument('--teams', action='store_true', help='Test/utilize the teams API (if provisioned on the jira instance)')

        return parser.parse_args()

    def run(self):

        if self.use_teams:
            teams = self.jt.teams()
            pprint.pprint(teams)
            for t in teams:
                print(t.title)

        df = self.build_report()

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter('pandas_simple.xlsx', engine='xlsxwriter')

        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Sprint Report', index=False)

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()


JiraProgramMetrics().run()
