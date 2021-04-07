from jira.client import JIRA
from jira.resources import Issue, Resource
import pprint
from random import choice, randint
from typing import List
import argparse
import os

# Story point sizes that are acceptable in a sprint
from jamp import JiraFieldMapper, JIRA_KEY_KEY

size_pts_seq = (1, 2, 3, 5, 8)


class BuildProgramInJira:

    def __init__(self):
        self._args = self.parse_args()
        self._project_key = self._args.project

        credential = os.environ['JIRA_PASSWORD']

        self.j = JIRA(server=self._args.url,
                      basic_auth=(self._args.user, credential),
                      options={
                          'agile_rest_path': 'agile'
                      })

        self.brds = self.j.boards()
        self._map = JiraFieldMapper(self.j._options, self.j._session)

    def jira_key(self, field_key):
        return self._map.jira_key(field_key)

    @property
    def use_teams(self):
        return self._args.teams

    def clean_up_sprints(self) -> None:
        for a in self.j.sprints(board_id=1):

            print(a, a.id)
            if self._project_key not in a.name:
                pass
            else:
                print(f'Deleting sprint {a}')
                a.delete()
                # j.delete_sprint(a.id)

    def build_story(self, summary=None, description=None, team_id=None, component=None, appendIndex=False) -> Issue:
        random_story_number = randint(1, 1000)
        if summary is None:
            summary_field = f'New issue'
        else:
            summary_field = summary

        if appendIndex:
            summary_field += f' {random_story_number}'

        field_dict = {
            self.jira_key("Project"): {JIRA_KEY_KEY: self._project_key},
            self.jira_key('Summary'): summary_field,
            self.jira_key('Description'): f'Look into this issue for the {random_story_number}th time',
            self.jira_key('Issue Type'): {'name': 'Story'},
            self.jira_key('Story Points'): choice(size_pts_seq)
        }
        if team_id:
            field_dict[self.jira_key('Team')] = str(team_id)

        if component:
            field_dict[self.jira_key('Components')] = [{'name': component}]

        issue = self.j.create_issue(fields=field_dict)
        return issue

    def build_pi(self, board_id: int, num_pi: int, num_sprints: int, sprint_prefix: str = 'Sprint') -> None:
        for pi_number in range(1, num_pi+1):
            for sprint_number in range(1, num_sprints+1):
                sprint_name = f'{sprint_prefix} {pi_number}.{sprint_number}'
                print(f'Creating sprint: {sprint_name}')
                sprint = self.j.create_sprint(board_id=board_id, name=sprint_name)
                issues_list: List[str] = []
                for t in range(1, 6):
                    if self.use_teams:
                        team_id = t
                        component = None
                    else:
                        team_id = None
                        component = f'Team {t}'

                    for i in range(1, randint(6, 11)):
                        issue = self.build_story(summary=f'User Story for {pi_number}.{sprint_number} hash',
                                                 team_id=team_id,
                                                 component=component,
                                                 appendIndex=True)
                        issues_list.append(issue.key)
                        pprint.pprint(issue)
                    self.j.add_issues_to_sprint(sprint_id=sprint.id, issue_keys=issues_list)

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Build Program in Jira')
        group = parser.add_mutually_exclusive_group()

        # group.add_argument('--user', default='steveteske@agileleadershipedge.com', help='User id for url')
        group.add_argument('--user', default='steveteske@agileleadershipedge.com', help='User id for Jira instance')
        group.add_argument('--url', default='https://ale-dev.atlassian.net', help='URL for api')
        group.add_argument('--project', default='JAMP', help='Jira project key')
        group.add_argument('--build', action='store_true', help='Build new program')
        group.add_argument('--teams', action='store_true', help='Use teams id to populate stories')
        group.add_argument('--clean', action='store_true', help='Cleanup existing program')

        return parser.parse_args()

    def run(self):

        if self._args.build:
            self.build_pi(1, 3, 5, sprint_prefix=f"API-{self._project_key} Sprint")

        if self._args.clean:
            print("Cleaning")
            self.clean_up_sprints()

        i = self.build_story()
        pprint.pprint(i)


BuildProgramInJira().run()
