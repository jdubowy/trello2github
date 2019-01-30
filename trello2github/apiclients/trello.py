import sys
import logging

from . import BaseApiClient

from ..prompts import single_line


class TrelloError(RuntimeError):
    pass

class TrelloClient(BaseApiClient):

    def __init__(self, api_key, trello_username, board_identifier,
            list_identifier, auth_token=None):
        self._api_key = api_key
        self._set_auth_token(auth_token)
        board_id = self._find_matching_board(trello_username, board_identifier)
        self._list_id = self._find_matching_list(board_id, list_identifier)

    def __del__(self):
        self._delete_auth_token()

    @property
    def api_root_url(self):
        return "https://api.trello.com/1/"

    @property
    def base_params(self):
        params = {"key": self._api_key}
        if self._auth_token:
            params['token'] = self._auth_token,
        return params

    ## Auth Tokens

    def _set_auth_token(self, auth_token):
        if auth_token:
            self._created_auth_token = False
            self._auth_token = auth_token
        else:
            self._created_auth_token = True
            sys.stdout.write("Go to the following url\n")
            sys.stdout.write(" https://trello.com/1/authorize?expiration=1day"
                "&name=trello2github&scope=read,write&response_type=token"
                "&key={}\n".format(self._api_key))
            sys.stdout.write("Copy the token, paste it here, and press return.\n")
            self._auth_token = single_line("Token")

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
        cards = []
        cards_json =  self._request('get', 'lists/{}/cards/open'.format(self._list_id))
        for card_json in cards_json:
            cards.append({
                "name": card_json["name"],
                "desc": card_json["desc"],
                "id": card_json["id"],
                "has_attachments": card_json['badges']['attachments'] > 0,
                "has_checklists": not not card_json.get("idChecklists")
            })
        return cards

    def get_checklists(self, card_id):
        checklists = []
        checklists_json = self._request('get',
            'cards/{}/checklists'.format(card_id))
        for cl_json in checklists_json:
            checklists.append({
                "name": cl_json["name"],
                "items": sorted([{k: i[k] for k in ('name', 'state')}
                    for i in cl_json["checkItems"]], key=lambda i: i['state'])
            })

        return checklists

    def get_attachements(self, card_id):
        attachments_json = self._request('get',
            'cards/{}/attachments'.format(card_id))
        return [{"url": a_json["url"]} for a_json in attachments_json]


    def archive_card(self, card_id, github_issue_url):
        if github_issue_url:
            logging.debug("Commenting on Trello card %s", card_id)
            path = 'cards/{}/actions/comments'.format(card_id)
            params = {
                "text": "Migrated to GitHub issue {}".format(github_issue_url)
            }
            self._request('post', path, params=params)

        logging.debug("Archiving Trello card %s", card_id)
        path = 'cards/{}/closed'.format(card_id)
        params = {"value": 'true'}
        return self._request('put', path, params=params)
