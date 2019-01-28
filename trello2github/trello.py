import sys
import logging

import requests

class TrelloError(RuntimeError):
    pass

class TrelloClient(object):

    API_ROOT_URL = "https://api.trello.com/1/"

    def __init__(self, api_key, trello_username, board_identifier, list_identifier, auth_token=None):
        self._api_key = api_key
        self._set_auth_token(auth_token)
        board_id = self._find_matching_board(trello_username, board_identifier)
        self._list_id = self._find_matching_list(board_id, list_identifier)

    def __del__(self):
        self._delete_auth_token()

    def _request(self, method, path, **query_params):
        url = self.API_ROOT_URL + path
        params = dict(key=self._api_key,**query_params)
        if self._auth_token:
            params['token'] = self._auth_token,
        resp = getattr(requests, method)(url=url, params=params)
        if resp.status_code != 200:
            raise TrelloError("Failed Trello request - {} {} {} -- {}".format(
                method.upper(), path, query_params, resp.status_code))
        return resp.json()

    ## Auth Tokens

    def _set_auth_token(self, auth_token):
        if auth_token:
            self._created_auth_token = False
            self._auth_token = auth_token
        else:
            self._created_auth_token = True
            self._auth_token = None
            sys.stdout.write("Go to the following url\n")
            sys.stdout.write(" https://trello.com/1/authorize?expiration=1day"
                "&name=trello2github&scope=read,write&response_type=token"
                "&key={}\n".format(self._api_key))
            sys.stdout.write("Copy the token, paste it here, and press return.\n")
            while not self._auth_token:
                sys.stdout.write("Token: ")
                self._auth_token = input().strip()

    def _delete_auth_token(self):
        if self._created_auth_token and self._auth_token:
            self._request('delete', 'tokens/{}/'.format(self._auth_token))

    ## Boards, lists, and cards

    def _find_matching_board(self, trello_username, board_identifier):
        boards_json = self._request('get', 'members/{}/boards'.format(trello_username))
        for b in boards_json:
            if board_identifier in (b['id'], b['name']):
                return b['id']

        raise TrelloError("Trello board '{}' not found".format(board_identifier))

    def _find_matching_list(self, board_id, list_identifier):
        lists_json = self._request('get','boards/{}/lists'.format(board_id))
        for l in lists_json:
            if list_identifier in (l['id'], l['name']):
                return l['id']

        raise TrelloError("Trello list '{}' not found".format(list_identifier))

    def get_cards(self):
        return self._request('get', 'lists/{}/cards/open'.format(self._list_id))

    def archive_card(self, card_id, github_issue_url):
        logging.debug("Archiving Trello card %s", card_id)
        # TODO:
        #   - post comment on trello card that it was migrated to GH, with GH link
        #   - archive card from Trello
