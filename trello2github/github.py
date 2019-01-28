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
        while True:
            prompt = ("Would you like to post the following issue to Github\n\n"
                "   " +  name + "\n\n   " + (description or ' (no description) '))
            options = (
                ('y', 'yes (post as is)'),
                ('n', 'no'),
                ('e', 'edit'),
                ('q', 'quit (exit)')
            )
            x = multiple_choice(prompt, options)

            if x == 'q':
                logging.info("Good Bye")
                sys.exit(0)
            elif x == 'n':
                return False
            elif x == 'y':
                # TODO:
                #   - post issue to GH - /repos/:owner/:repo/issues
                #   - post card to GH board (if necessary)
                #   - move issue to last on project board

                return # TODO: return url

            # else, edit and loop through again
            sys.stdout.write(" Title: ")
            name = input().strip()
            sys.stdout.write(" Description: ")
            description = input().strip()
