"""
TODO:
 - Create base client class to DRY up code between trello and github clients
"""

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

    def __del__(self):
        self._delete_access_token()

    def _request(self, method, path, headers={}, **params):
        url = self.API_ROOT_URL + path
        params = dict(access_token=self._access_token, **params)
        resp = getattr(requests, method)(url=url, headers=headers, params=params)
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

    def _get_projects(self):
        path = 'repos/{}/{}/projects'.format(self._owner, self._repo_name)
        headers = {"Accept": "application/vnd.github.inertia-preview+json"}
        projects_json = self._request('get', path, headers=headers)
        return [{k: p[k] for k in ('id', 'url', 'html_url', 'name')} for p in projects_json]

    def _set_project(self):
        projects = self._get_projects()
        if not projects:
            logging.error("*** No projects associated with {} repo".format(self._repo_name))
            logging.error("*** Create a project and rerun this script")
            sys.exit(1)
        elif len(projects) == 1:
            self._project_id = projects[0]['id']
        else:
            prompt = "Pick a project"
            options = [(i, e['name']) for i, e in enumerate(projects)] + [('q','quit (exit)')]
            x = int(multiple_choice(prompt, options))
            self._project_id = projects[x]['id']


    ## Issues

    def post_issue(self, title, body):
        logging.debug("Posting GitHub issue %s", title)
        while True:
            prompt = ("Would you like to post the following issue to Github\n\n"
                "   " +  title + "\n\n   " + (body or ' (no body) '))
            options = (
                ('y', 'yes (post as is)'),
                ('n', 'no'),
                ('e', 'edit')
            )
            x = multiple_choice(prompt, options)

            if x == 'n':
                return False
            elif x == 'y':
                path = 'repos/{}/{}/issues'.format(self._owner, self._repo_name)
                params = {"title": title, "body": body}
                resp_json = self._request('post', path, **params)
                import pdb;pdb.set_trace()
                # TODO:
                #   - post card to GH board (if necessary)
                #   - move issue to last on project board

                return resp_json['url']

            # else, edit and loop through again
            sys.stdout.write(" Title: ")
            title = input().strip()
            sys.stdout.write(" Body: ")
            body = input().strip()
