import json
import logging
import re
import sys

from . import BaseApiClient

from ..prompts import single_line, singemultiple_choice, edit_in_text_editor


class EmptyResourceList(RuntimeError):
    pass

class GitHubClient(BaseApiClient):

    def __init__(self, owner, repo_name, access_token=None,
            title_prefixes_to_remove=[]):
        self._owner = owner
        self._repo_name = repo_name
        self._repo_name_strippers = [
            re.compile("(?i)^\w*{}\w*:\w*".format(self._repo_name))
        ]
        for p in title_prefixes_to_remove:
            self._repo_name_strippers.append(
                re.compile("(?i)^\w*{}\w*".format(p)))
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

    def _request(self, method, path, headers={}, params={}, data=None):
        headers["Accept"] = "application/vnd.github.inertia-preview+json"
        return super()._request(method, path, headers=headers, params=params,
            data=data)

    ## Access Token

    def _set_access_token(self, access_token):
        if access_token:
            self._created_access_token = False
            self._access_token = access_token
        else:
            self._created_access_token = True
            sys.stdout.write("Go to the following url\n")
            sys.stdout.write(" https://github.com/settings/tokens/new\n")
            sys.stdout.write("Generate a new access token with repo privileges,"
                " copy it, paste it here, and press return.\n")
            self._access_token = single_line("Token")

    def _delete_access_token(self):
        if self._created_access_token and self._access_token:
            # TODO: delete, if possible
            pass

    ## Project

    def _select_resource(self, resource_type, path):
        json_list = self._request('get', path)
        if not json_list:
            # logging.error("*** No {} associated with {} repo".format(
            #     resource_type, self._repo_name))
            # logging.error("*** Create a project and rerun this script")
            raise EmptyResourceList()

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

    @property
    def project_api_path(self):
        return 'repos/{}/{}/projects'.format(self._owner, self._repo_name)

    def _create_project(self):
        path = self.project_api_path
        data = {"name": "{} TODOs".format(self._repo_name)}
        r = self._request('post', path, data=data)
        return r['id'], r['name']

    def _set_project(self):
        try:
            self._project_id, self._project_name = self._select_resource(
                'project', self.project_api_path)
        except EmptyResourceList as e:
            self._project_id, self._project_name = self._create_project()

    def _create_project_column(self):
        path = "projects/{}/columns".format(self._project_id)
        data = {"name": "To do"}
        r = self._request('post', path, data=data)
        return r['id'], r['name']

    def _set_project_column(self):
        try:
            self._columns_id, self._column_name = self._select_resource('project column',
                'projects/{}/columns'.format(self._project_id))
        except EmptyResourceList as e:
            self._columns_id, self._column_name= self._create_project_column()


    ## Issues

    def _create_checklists_markdown(self, checklists):
        if not checklists:
            return ""

        text = "## Checklists\n"
        for cl in checklists:
            text += "\n### {}\n\n".format(cl["name"])
            for i in cl['items']:
                text += "- [{}] {}\n".format(
                    'x' if i['state'] == 'complete' else ' ', i['name'])
        text += '\n----\n\n'
        return text

    def _create_attachments_markdown(self, attachments):
        if not attachments:
            return ""

        text = '\n\n----\n\n## Attachments\n\n'
        for a in attachments:
            text += "![{url}]({url})".format(url=a['url'])

        return text

    def post_issue(self, title, body, checklists, attachments):
        """
        TODO: Implement better means of communicating to caller - something
            other than returning status, url tuple
        """
        for s in self._repo_name_strippers:
            title = s.sub("", title).strip()

        # put checklists at beginning of body
        body = (self._create_checklists_markdown(checklists) +  body +
            self._create_attachments_markdown(attachments))

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
                body = body + "\n\n***(Programatically migrated from Trello)***"
                data = {"title": title, "body": body}
                new_issue = self._request('post', path, data=data)

                try:
                    logging.debug("Adding project card")
                    path = "projects/columns/{}/cards".format(self._columns_id)
                    data = {"content_id": new_issue['id'], "content_type": "Issue"}
                    new_card = self._request('post', path, data=data)

                    logging.debug("Moving card to top of board")
                    path = "projects/columns/cards/{}/moves".format(new_card['id'])
                    data = {"position": "top"}
                    new_card = self._request('post', path, data=data)

                except:
                    logging.error("Failed to add issue %s to project board",
                        new_card['name'])

                return "Posted", new_issue['html_url']

            # else, edit and loop through again
            title = edit_in_text_editor("title", title)
            body = edit_in_text_editor("body", body)
