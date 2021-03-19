from jamp.resources import SprintReport, VelocityReport


class SprintMetrics:

    def __init__(self, sprint_id: int, sprint_report: SprintReport, velocity_report: VelocityReport):
        self._sprint_report = sprint_report
        self._velocity_report = velocity_report
        self._sprint_id = sprint_id
        self._velocity_stat = self._retrieve_velocity_stat()

    def _retrieve_velocity_stat(self):
        stat = self._velocity_report.velocityStatEntries
        value = getattr(stat, f'{self._sprint_id}')
        return value

    @property
    def completed_issues_delta_sum(self):
        return self._sprint_report.self._sprint_report.completedIssuesInitialEstimateSum \
                          - self._sprint_report.completedIssuesEstimateSum

    @property
    def incomplete_issues_delta_sum(self):
        return self._sprint_report.self.issuesNotCompletedInitialEstimateSum \
                           - self._sprint_report.self.issuesNotCompletedEstimateSum

    @property
    def punted_issues_delta_sum(self):
        return self._sprint_report.self.puntedIssuesInitialEstimateSum \
                       - self._sprint_report.self.puntedIssuesEstimateSum

    @property
    def added_sum(self):
        return self._sprint_report.completedIssuesInitialEstimateSum

    @property
    def punted_sum(self):
        return self._sprint_report.puntedIssuesEstimateSum

    @property
    def complete_issues_estimate_sum(self):
        return self._sprint_report.completedIssuesEstimateSum

    @property
    def velocity_estimated(self):
        return self._velocity_stat.estimated.value

    @property
    def velocity_completed(self):
        return self._velocity_stat.completed.value

    def completion_ratio(self) -> float:
        return self.velocity_completed / self.velocity_estimated


class ProgramReport:
    pass

