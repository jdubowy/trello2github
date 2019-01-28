import logging
import sys

from .prompts import multiple_choice

class GitHubClient(object):

    def __init__(self, api_key, owner, repo_name):
        self._api_key = api_key
        self._owner = owner
        self._repo_name = repo_name

    def post_issue(self, name, description):
        logging.debug("Posting GitHub issue %s", name)
        #/repos/:owner/:repo/issues
        # TODO:
        #    - prompt user to see if they want to migrate the card (showing all
        #      text that will be transfered) include options yes, no, quit (exit)
        #    - if yes:
        #     - prompt to confirm or edit issue title
        #     - prompt to confirm or edit issue description
        #     - post issue to GH
        #     - post card to GH board (if necessary)
        #     - move issue to last on project board
        #     - return url
