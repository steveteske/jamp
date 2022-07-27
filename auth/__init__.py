import os

JIRA_PASSWORD_ENV = 'JIRA_PASSWORD'


class Credential:

    def __init__(self, user: str):
        self._username = user
        if JIRA_PASSWORD_ENV not in os.environ:
            raise KeyError(f"The environment variable '{JIRA_PASSWORD_ENV}'"
                           f" is required to authenticate with the Jira Server.")

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return os.environ[JIRA_PASSWORD_ENV]