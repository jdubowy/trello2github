import abc
import json
import logging

import requests


class ApiClientError(RuntimeError):
    pass

class BaseApiClient(object, metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def api_root_url(self):
        pass

    @property
    @abc.abstractmethod
    def base_params(self):
        pass

    def _request(self, method, path, headers={}, params={}, data=None):
        url = self.api_root_url + path
        params = dict(self.base_params, **params)
        data = data and json.dumps(data)
        resp = getattr(requests, method)(url=url, headers=headers,
            params=params, data=data)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise ApiClientError("Failed {} request - {} {} {} {} {} -- {}".format(
                self.__class__.__name__, method.upper(), path, params, data,
                headers, resp.status_code))
        return resp.json()
