from typing import List

import pandas as pd
from jira import JIRA, JIRAError
import pprint
import argparse

from auth import Credential
from jamp import JiraFieldMapper, NAN, _parse_server
from jamp.client import JIRAReports, JIRATeams
from jamp.resources import CfdReport
from jamp.confluence import JampConfluence
from jamp.plot import MetricPlot

class JiraProgramMetrics:

    def __init__(self):
        self._args = self.parse_args()
        self._server = _parse_server(self._args)

        cred = Credential(self._args.user)

        # JIRA for all normal Jira activity (Boards, Sprints, Issues, etc.)
        self.jira_client = JIRA(server=self._server,
                                basic_auth=(cred.username, cred.password),
                                options={
                          'agile_rest_path': 'agile'
                      })

        # JIRA_Reports used only for reporting, not for general Jira access
        self.reports_client = JIRAReports(server=self._server,
                                          basic_auth=(cred.username, cred.password))

        if self.use_teams:
            # JIRA for all normal Jira activity (Boards, Sprints, Issues, etc.)
            self.teams_client = JIRATeams(server=self._server,
                                          basic_auth=(cred.username, cred.password),
                                          options={
                                       'agile_rest_path': 'teams-api'
                                   })

        self._map = JiraFieldMapper(self.jira_client._options, self.jira_client._session)

        if self._args.page:
            self._confluence = JampConfluence(self._server, cred)
            self._plotter = MetricPlot(self._args.image)
    def jira_key(self, field_key):
        return self._map.jira_key(field_key)

    @property
    def cfd_requested(self) -> bool:
        return self._args.cfd is not None

    @property
    def cfd_filename(self) -> bool:
        return self._args.cfd

    @property
    def use_teams(self):
        return self._args.teams

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Build Program in Jira')
        # group = parser.add_mutually_exclusive_group()
        parser.add_argument('--user', required=True, type=str, help='User name')
        parser.add_argument('--server', required=True, type=str,
                            help='Jira server address (e.g. https://ale-dev.atlassian.net).'
                                 'Typically only the server name is required, and no additional'
                                 'path elements are needed in the URL.')
        parser.add_argument('--space', type=str,
                            help='Confluence space to write the report')
        parser.add_argument('--page', type=str,
                            help='Confluence page to write the report')
        parser.add_argument('--force_full_url', action='store_true',
                            help='Force server parameter to use the full path. Typically the server '
                                 'name is truncated to include only protocol server name and remove any '
                                 'extra path elements.')
        parser.add_argument('--cfd', type=str,
                            help='Create a Cumulative Flow Diagram output file with the specified file name')
        parser.add_argument('--board', type=str,
                            help='Board name and matching criteria which uses the following '
                                 'syntax: [<name>:<match>;<str2>:<match2>;...] where match is one of'
                                 ' MATCH_EXACT | MATCH_STARTS_WITH.  (e.g. --board JAMP:MATCH_EXACT)')
        parser.add_argument('--teams', action='store_true',
                            help='Test/utilize the teams API (if provisioned on the jira instance)')
        parser.add_argument('--file', type=str, required=True,
                            help='file name for excel output file with suffix ".xlsx"')
        parser.add_argument('--image', type=str, required=True,
                            help='file name for image file')

        return parser.parse_args()

    def board_list(self):
        boards = []
        if not self._args.board:
            return self.jira_client.boards(maxResults=None)

        filters = self._args.board.split(';')
        for f in filters:
            tuple = f.split(":")
            if len(tuple) == 1:
                command = 'MATCH_STARTS_WITH'
                pattern = tuple[0]
            elif len(tuple) == 2:
                (pattern, command) = tuple
            else:
                raise ValueError(f"Poorly formed filter {f}. Must be PATTERN:COMMAND, where"
                                 f"COMMAND is either 'MATCH_STARTS_WITH' or 'MATCH_EXACT'")

            for b in self.jira_client.boards(type='scrum', maxResults=None):
                print(b.name)
                if "IDAP" in b.name:
                    pprint.pprint(b.raw)
                if command == 'MATCH_STARTS_WITH' and b.name.startswith(pattern):
                    boards.append(b)
                elif command == 'MATCH_EXACT' and b.name == pattern:
                    boards.append(b)

        return boards

    def build_cfd(self) -> List[CfdReport]:
        """
        """
        cfd_list = []
        for board in self.board_list():
            print(board, "hi")
            cfd = self.reports_client.cfd_report(board_id=board.id)
            cfd_list.append(cfd)
        return cfd_list

    def build_report(self) -> pd.DataFrame:
        """
        """

        HEADERS = ("Team",
                   "Sprint",
                   "State",
                   "Story Points Committed",
                   "Story Points Committed VC",
                   "Story Points Added",
                   "Story Points Removed",
                   "Story Points Not Completed",
                   "Story Points Completed",
                   "Story Points Completed VC",
                   "% Complete",
                   '# Issues Committed',
                   "# Issues Added",
                   "# Issues Removed",
                   "# Issues Not Completed",
                   "# Issues Completed",
                   "% Complete",
                   )

        data = []
        for board in self.board_list():
            vr = self.reports_client.velocity_report(board_id=board.id)
            print(f"Examining board: {board.name} ({board.id})")
            if board.type != 'scrum':
                continue

            for sprint in self.jira_client.sprints(board_id=board.id, maxResults=None):
                try:
                    # Once during a run, Jira returned a internal error
                    # ... HTTPS 500 "Passed List had more than one value."
                    # ... Catch the error and continue on.
                    print(f"Examining sprint: {sprint.name} ({sprint.id})")

                    sr = self.reports_client.sprint_report(board_id=board.id, sprint_id=sprint.id)
                except JIRAError as err:
                    print("JIRAError occured: ", err)
                    continue

                if "IDAP" in board.name:
                    pprint.pprint(sr.raw)

                if sr.committed > 0.0:
                    percent_complete = sr.completedIssuesEstimateSum / sr.committed
                else:
                    percent_complete = NAN

                data.append((board.name,
                             sr.sprint.name,
                             sr.sprint.state,
                             sr.committed,
                             vr.committed(sprint.id),
                             sr.added_sum,
                             sr.puntedIssuesEstimateSum,
                             sr.issuesNotCompletedEstimateSum,
                             sr.completedIssuesEstimateSum,
                             vr.completed(sprint.id),
                             percent_complete,
                             sr.committed_count,
                             sr.added_count,
                             sr.puntedIssuesCount,
                             sr.issuesNotCompletedInCurrentSprintCount,
                             sr.completedIssuesCount,
                             sr.percent_complete_count,

                             ))

        df = pd.DataFrame.from_records(data, columns=HEADERS)
        return df



    def run(self):

        if self.use_teams:
            self.extract_teams()

        if self.cfd_requested:
            self.build_cfd_report()


        else:
            df = self.build_report()
            self.build_sprint_report(df)

            if self._args.page:
                self._plotter.plot(df)
                self._confluence.read(self._args.space, self._args.page)
                self._confluence.attach(self._args.space, self._args.page, self._args.file)
                self._confluence.attach(self._args.space, self._args.page, self._args.image)
    def build_sprint_report(self, df: pd.DataFrame):
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(self._args.file, engine='xlsxwriter')
        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Sprint Report', index=False)
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

    def build_cfd_report(self):
        cfd_list = self.build_cfd()
        writer = pd.ExcelWriter(self.cfd_filename, engine='xlsxwriter')
        MAX_TAB_NAME_LENGTH = 30
        board_name_max = MAX_TAB_NAME_LENGTH - len('CFD ')
        for cfd in cfd_list:
            df = cfd.report()
            df.to_excel(writer, sheet_name=f'CFD {cfd.board_name[:board_name_max]}', index=False)
        writer.save()

    def extract_teams(self):
        teams = self.teams_client.teams()
        pprint.pprint(teams)
        for t in teams:
            print(t.title)


if __name__ == "__main__":
    JiraProgramMetrics().run()
