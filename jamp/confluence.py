from atlassian import Confluence
from auth import Credential


class JampConfluence:

    def __init__(self, url: str, credential: Credential):
        self._cred = credential
        self._confluence = Confluence(
            url=url,
            username=self._cred.username,
            password=self._cred.password)

    def read(self, space: str, page: str):
        page = self._confluence.get_page_by_title(space, page)
        print(page)

    def attach(self, space: str, page: str, filename: str):
        self._confluence.attach_file(filename=filename,space=space,title=page)
