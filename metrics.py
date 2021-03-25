import sys

import pandas as pd
from jira import JIRA
import pprint
import argparse
import os

import jamp
from jamp import JiraFieldMapper
from jamp.client import JIRAReports, JIRATeams


class JiraProgramMetrics:

    def __init__(self):
        self._args = self.parse_args()
        self._server = self._parse_server()

        if jamp.JIRA_PASSWORD_ENV not in os.environ:
            raise KeyError(f"The environment variable '{jamp.JIRA_PASSWORD_ENV}' is required "
                           "to authenticate with the Jira Server.")

        credential = os.environ[jamp.JIRA_PASSWORD_ENV]

        # JIRA for all normal Jira activity (Boards, Sprints, Issues, etc.)
        self.j = JIRA(server=self._server,
                      basic_auth=(self._args.user, credential),
                      options={
                          'agile_rest_path': 'agile'
                      })

        # JIRA_Reports used only for reporting, not for general Jira access
        self.jr = JIRAReports(server=self._server,
                              basic_auth=(self._args.user, credential))

        if self.use_teams:
            # JIRA for all normal Jira activity (Boards, Sprints, Issues, etc.)
            self.jt = JIRATeams(server=self._server,
                                basic_auth=(self._args.user, credential),
                                options={
                                       'agile_rest_path': 'teams-api'
                                   })

        self._map = JiraFieldMapper(self.j._options, self.j._session)

    def jira_key(self, field_key):
        return self._map.jira_key(field_key)

    def _parse_server(self):
        the_split = self._args.server.split('/')
        print(the_split)
        if len(the_split) > 3:
            print("WARNING: The server name has been truncated to "
                  f"{the_split[0]}//{the_split[2]})."
                  f"To force the full path, use --force_full_url parameter")

        if len(the_split) < 3:
            raise ValueError("The server name must be in the form of http|https://<domain_name>")

        server_name = f"{the_split[0]}//{the_split[2]}"

        if self._args.force_full_url:
            return self._args.server
        else:
            return server_name

    @property
    def use_teams(self):
        return self._args.teams

    def board_list(self):
        boards = []
        filters = self._args.board.split(';')

        for f in filters:
            (pattern, command) = f.split(":")
            for b in self.j.boards():
                if command == 'MATCH_STARTS_WITH' and b.name.startswith(pattern):
                    boards.append(b)
                elif command == 'MATCH_EXACT' and b.name == pattern:
                    boards.append(b)

        return boards

    def build_report(self) -> pd.DataFrame:

        HEADERS = ("Team",
                   "Sprint",
                   "Committed",
                   "Committed VC",
                   "Added",
                   "Removed",
                   "Not Completed",
                   "Completed",
                   "Completed VC",
                   "% Complete")

        data = []
        for board in self.board_list():
            vr = self.jr.velocity_report(board_id=board.id)
            print(f"Examining board: {board.name} ({board.id})")
            if board.type != 'scrum':
                continue

            for sprint in self.j.sprints(board_id=board.id):
                print(f"Examining sprint: {sprint.name} ({sprint.id})")
                sr = self.jr.sprint_report(board_id=board.id, sprint_id=sprint.id)

                if sr.committed > 0.0:
                    percent_complete = sr.completedIssuesEstimateSum / sr.committed
                else:
                    percent_complete = float("NaN")

                data.append((board.name,
                             sr.sprint.name,
                             sr.committed,
                             vr.committed(sprint.id),
                             sr.added_sum,
                             sr.puntedIssuesEstimateSum,
                             sr.issuesNotCompletedEstimateSum,
                             sr.completedIssuesEstimateSum,
                             vr.completed(sprint.id),
                             percent_complete
                             ))

        df = pd.DataFrame.from_records(data, columns=HEADERS)
        return df

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Build Program in Jira')
        # group = parser.add_mutually_exclusive_group()
        parser.add_argument('--user', required=True, type=str, help='User name')
        parser.add_argument('--server', required=True, type=str,
                            help='Jira server address (e.g. https://ale-dev.atlassian.net).'
                                 'Typically only the server name is required, and no additional'
                                 'path elements are needed in the URL.')
        parser.add_argument('--force_full_url', action='store_true',
                            help='Force server parameter to use the full path. Typically the server '
                                 'name is truncated to include only protocol server name and remove any '
                                 'extra path elements.')
        parser.add_argument('--board', type=str,
                            help='Board name and matching criteria which uses the following '
                                 'syntax: [<name>:<match>;<str2>:<match2>;...] where match is one of'
                                 ' MATCH_EXACT | MATCH_STARTS_WITH.  (e.g. --board JAMP:MATCH_EXACT)')
        parser.add_argument('--teams', action='store_true',
                            help='Test/utilize the teams API (if provisioned on the jira instance)')

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


if __name__ == "__main__":
    JiraProgramMetrics().run()
