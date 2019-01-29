"""
TODO:
 - Create base client class to DRY up code between trello and github clients
"""

import json
import logging
import re
import sys

from . import BaseApiClient

from ..prompts import multiple_choice


class GitHubClient(BaseApiClient):

    def __init__(self, owner, repo_name, access_token=None):
        self._owner = owner
        self._repo_name = repo_name
        self._repo_name_stripper = re.compile("(?i)^\w*{}\w*:".format(self._repo_name))
        self._set_access_token(access_token)
        self._set_project()
        self._set_project_column()

    def __del__(self):
        self._delete_access_token()

    @property
    def api_root_url(self):
        return "https://api.github.com/"

    @property
    def base_params(self):
        return {"access_token": self._access_token}

    ## Access Token

    def _set_access_token(self, access_token):
        if access_token:
            self._created_access_token = False
            self._access_token = access_token
        else:
            self._created_access_token = True
            self._access_token = None
            sys.stdout.write("Go to the following url\n")
            sys.stdout.write(" https://github.com/settings/tokens/new")
            sys.stdout.write("Generate a new access token, copy it, "
                "paste it here, and press return.\n")
            while not self._access_token:
                sys.stdout.write("Token: ")
                self._access_token = input().strip()

    def _delete_access_token(self):
        if self._created_access_token and self._access_token:
            # TODO: delete, if possible
            pass

    ## Project

    def _select_resource(self, resource_type, path):
        headers = {"Accept": "application/vnd.github.inertia-preview+json"}
        json_list = self._request('get', path, headers=headers)
        if not json_list:
            logging.error("*** No {} associated with {} repo".format(
                resource_type, self._repo_name))
            logging.error("*** Create a project and rerun this script")
            sys.exit(1)

        resources = [{
            k: p.get(k) for k in ('id', 'url', 'html_url', 'name')
        } for p in json_list]

        if len(resources) == 1:
            return resources[0]['id'], resources[0]['name']
        else:
            prompt = "Pick a {}".format(resource_type)
            options = [(i, e['name']) for i, e in enumerate(resources)]
            x = int(multiple_choice(prompt, options))
            return resources[x]['id'], resources[x]['name']

    def _set_project(self):
        self._project_id, self._project_name = self._select_resource('project',
            'repos/{}/{}/projects'.format(self._owner, self._repo_name))

    def _set_project_column(self):
        self._columns_id, self._column_name = self._select_resource('project column',
            'projects/{}/columns'.format(self._project_id))


    ## Issues

    def post_issue(self, title, body):
        """
        TODO: Implement better means of communicating to caller - something
            other than returning status, url tuple
        """
        title = self._repo_name_stripper.sub("", title).strip()

        while True:
            prompt = ("Would you like to post the following issue to Github\n\n"
                + ("*" * 80) + "\n" + "* Title\n\n" + title + "\n\n"
                + ("*" * 80) + "\n" + "* Body\n\n" + (body or ' (no body) ')
                + "\n\n" + ("*" * 80))
            options = [
                ('p', 'Post issue is'),
                ('e', 'Edit'),
                ('s', 'Skip'),
                ('a', 'Archive trello card without posting issue')
            ]
            x = multiple_choice(prompt, options)

            if x == 's':
                return "Skipped", None
            elif x == 'a':
                return "Archive", None
            elif x == 'p':
                logging.debug("Posting GitHub issue %s", title)
                path = 'repos/{}/{}/issues'.format(self._owner, self._repo_name)
                body = body + "\n\nProgramatically migrated from Trello"
                data = {"title": title, "body": body}
                new_issue = self._request('post', path, data=data)

                try:
                    logging.debug("Adding project card")
                    headers = {"Accept": "application/vnd.github.inertia-preview+json"}
                    path = "projects/columns/{}/cards".format(self._columns_id)
                    data = {"content_id": new_issue['id'], "content_type": "Issue"}
                    new_card = self._request('post', path, headers=headers, data=data)

                    logging.debug("Moving card to end of board")
                    path = "projects/columns/cards/{}/moves".format(new_card['id'])
                    data = {"position": "top"}
                    new_card = self._request('post', path, headers=headers, data=data)

                except:
                    logging.error("Failed to add issue %s to project board",
                        new_card['name'])

                return "Posted", new_issue['html_url']

            # else, edit and loop through again
            sys.stdout.write(" Title: ")
            title = input().strip()
            sys.stdout.write(" Body: ")
            body = input().strip()
