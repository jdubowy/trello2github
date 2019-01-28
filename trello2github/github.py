"""
TODO:
 - Create base client class to DRY up code between trello and github clients
"""

import json
import logging
import sys

import requests

from .prompts import multiple_choice

class GitHubError(RuntimeError):
    pass

class GitHubClient(object):

    API_ROOT_URL = "https://api.github.com/"

    def __init__(self, owner, repo_name, access_token=None):
        self._owner = owner
        self._repo_name = repo_name
        self._set_access_token(access_token)
        self._set_project()
        self._set_project_column()

    def __del__(self):
        self._delete_access_token()

    def _request(self, method, path, headers={}, params={}, data=None):
        url = self.API_ROOT_URL + path
        params = dict(access_token=self._access_token, **params)
        data = data and json.dumps(data)
        resp = getattr(requests, method)(url=url, headers=headers,
            params=params, data=data)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise GitHubError("Failed GitHub request - {} {} {} -- {}".format(
                method.upper(), path, params, resp.status_code))
        return resp.json()

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


    def _select_item(self, resource_type, path):
        headers = {"Accept": "application/vnd.github.inertia-preview+json"}
        json_list = self._request('get', path, headers=headers)
        if not json_list:
            logging.error("*** No {} associated with {} repo".format(
                resource_type, self._repo_name))
            logging.error("*** Create a project and rerun this script")
            sys.exit(1)

        l = [{k: p[k] for k in ('id', 'url', 'html_url', 'name')} for p in json_list]
        if len(projects) == 1:
            return projects[0]['id'], projects[0]['name']
        else:
            prompt = "Pick a {}".format(resource_type)
            options = [(i, e['name']) for i, e in enumerate(projects)] + [('q','quit (exit)')]
            x = int(multiple_choice(prompt, options))
            return projects[x]['id'], projects[x]['name']

    def _set_project(self):
        self._project_id, self._project_name = self._select_item('project',
            'repos/{}/{}/projects'.format(self._owner, self._repo_name))

    def _set_project_column(self):
        self._columns_id, self._column_name = self._select_item('project column'
            '/projects/:project_id/columns'.format(self._project_id))


    ## Issues

    def post_issue(self, title, body):
        while True:
            prompt = ("Would you like to post the following issue to Github\n\n"
                "   " +  title + "\n\n   " + (body or ' (no body) '))
            options = [
                ('y', 'yes (post as is)'),
                ('n', 'no'),
                ('e', 'edit')
            ]
            x = multiple_choice(prompt, options)

            if x == 'n':
                return False
            elif x == 'y':
                logging.debug("Posting GitHub issue %s", title)
                path = 'repos/{}/{}/issues'.format(self._owner, self._repo_name)
                data = {"title": title, "body": body}
                new_issue = self._request('post', path, data=data)

                logging.debug("Adding project card")
                path "/projects/columns/{}/cards".format(self._columns_id)
                data = {"content_id": new_issue['id'], "content_type": "Issue"}
                new_card = self._request('post', path, data=data)

                logging.debug("Moving card to end of board")
                path = "/projects/columns/cards/{}/moves".format(new_card['id'])
                data = {"position": "bottom"}
                new_card = self._request('post', path, data=data)

                return new_issue['html_url']

            # else, edit and loop through again
            sys.stdout.write(" Title: ")
            title = input().strip()
            sys.stdout.write(" Body: ")
            body = input().strip()
