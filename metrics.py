import pprint
from random import choice, randint
from typing import List

import pandas as pd
from jira import JIRA
from jira.resources import GreenHopperResource
from jira.resources import Issue


class SprintReport(GreenHopperResource):
    """A SprintReport."""
    def __init__(self, options, session, raw=None):
        options['agile_rest_path'] = 'greenhopper'
        path = 'rapid/charts/sprintreport?{0}'
        GreenHopperResource.__init__(self, path, options, session, raw)

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
        This overridden __getattr__ method allos  direct access the json named dict elements.

        If the attribute is not found localy, call the parent to utilize the super class
        __getattr__.

        :param item: attribute name requested by the caller
        :return: Any
        """
        STATS=(  'completedIssuesInitialEstimateSum',
                 'completedIssuesEstimateSum',
                 'allIssuesEstimateSum',
                 'issuesNotCompletedInitialEstimateSum',
                 'issuesNotCompletedEstimateSum',
                 'puntedIssuesInitialEstimateSum',
                 'puntedIssuesEstimateSum',
                 'issuesCompletedInAnotherSprintInitialEstimateSum',
                 'issuesCompletedInAnotherSprintEstimateSum',
                 'issuesCompletedInAnotherSprintEstimateSum')

        LISTS=( 'completedIssues',
                'issuesNotCompletedInCurrentSprint',
                'puntedIssues',
                'issuesCompletedInAnotherSprint',
                'issueKeysAddedDuringSprint')

        COUNTS=[x+'Count' for x in LISTS]

        if item in STATS or item in LISTS:
            return self.normalize_contents_stat(getattr(self.contents, item))
        if item in COUNTS:
            base_item = item[:-len('Count')]
            return len(getattr(self.contents, base_item))
        else:
            return super().__getattr__(item)


class JIRA_Reports(JIRA):

    def sprint_report(self, board_id, sprint_id) -> SprintReport:
        # ...rest/greenhopper/1.0/rapid/charts/sprintreport?rapidViewId=1&sprintId=1
        r_json = self._get_json(f'rapid/charts/sprintreport?rapidViewId={board_id}&sprintId={sprint_id}',
                                base=self.AGILE_BASE_URL)
        # This is a hack to make the Sprint Report a resource, even if it's not
        # ...really a resource.
        if 'id' not in r_json:
            r_json['id'] = f'rapidViewId={board_id}&sprintId={sprint_id}'

        sprint_report = SprintReport(self._options, self._session, r_json)
        return sprint_report


# Story point sizes that are acceptable in a sprint
size_pts_seq = (1, 2, 3, 5, 8)

print("hello world")
j = JIRA(server='http://localhost:8080',
              basic_auth=('steveteske', 's3r34nn4'),
              options={
                  'agile_rest_path': 'agile'
              })

jr = JIRA_Reports(server='http://localhost:8080',
                  basic_auth=('steveteske', 's3r34nn4'))

brds = j.boards()
pprint.pprint(brds)


def clean_up_sprints() -> None:
    for a in j.sprints(board_id=1):

        print(a, a.id)
        if "Sample" in a.name:
            pass
        else:
            print(f'Deleting sprint {a}')
            a.delete()
            # j.delete_sprint(a.id)


def build_story(summary=None, description=None, appendIndex=False) -> Issue:
    random_story_number = randint(1, 100)
    if summary is None:
        summary_field = f'New issue'
    else:
        summary_field = summary

    if appendIndex:
        summary_field += f' {random_story_number}'

    field_dict = {
        'project': {'key': 'AV'},
        'summary': summary_field,
        'description': f'Look into this issue for the {random_story_number}th time',
        'issuetype': {'name': 'Story'},
        'customfield_10111': choice(size_pts_seq)
    }
    issue = j.create_issue(fields=field_dict)
    return issue


def build_pi(board_id: int, num_pi: int, num_sprints: int, sprint_prefix: str = 'Sprint') -> None:
    for pi_number in range(1, num_pi+1):
        for sprint_number in range(1, num_sprints+1):
            sprint_name = f'{sprint_prefix} {pi_number}.{sprint_number}'
            print(f'Creating sprint: {sprint_name}')
            sprint = j.create_sprint(board_id=board_id, name=sprint_name)
            issues_list: List[str] = []
            for i in range(1, randint(6, 11)):
                issue = build_story(summary=f'User Story for {pi_number}.{sprint_number} hash', appendIndex=True)
                issues_list.append(issue.key)
                pprint.pprint(issue)
            j.add_issues_to_sprint(sprint_id=sprint.id, issue_keys=issues_list)


def build_report(board_id, sprint_id) -> pd.DataFrame:
    HEADERS = ("Sprint", "Completed", "Completed Final", "All","Not Complete Count")
    board_list = j.boards()
    data = []
    for board in board_list:
        for sprint in j.sprints(board_id=board.id):
            print(board.id, sprint.id)
            sr = jr.sprint_report(board_id=board.id, sprint_id=sprint.id)

            value = sr.completedIssuesInitialEstimateSum
            print(value)
            data.append((sr.sprint.name,
                         sr.completedIssuesInitialEstimateSum,
                         sr.completedIssuesEstimateSum,
                         sr.allIssuesEstimateSum,
                         sr.issuesNotCompletedInCurrentSprintCount))

    df = pd.DataFrame.from_records(data, columns=HEADERS)
    return df

# build_pi(1, 3, 5)
i = build_story()
# clean_up_sprints()
df = build_report(1, 1)
print(i)

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter('pandas_simple.xlsx', engine='xlsxwriter')

# Convert the dataframe to an XlsxWriter Excel object.
df.to_excel(writer, sheet_name='Sprint Report')

# Close the Pandas Excel writer and output the Excel file.
writer.save()
