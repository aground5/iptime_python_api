import time
from time import sleep

from requests import Session
from datetime import datetime

from .exceptions import ServiceCgiExceptions
from .entities import Router, FirmwareUpgradeStatus, Station


class IPTimeAPIClass:
    def __init__(self, ip, username, password):
        self._username = username
        self._password = password

        self.session = Session()
        self.session.headers.update({
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache',
            'Origin': f'http://{ip}',
            'Referer': f'http://{ip}/ui',
            'User-Agent': 'ipTIME_API_0.1',
        })

        self.SERVICE_CGI = f'http://{ip}/cgi/service.cgi'
        self.EASYMESH_CGI = f'http://{ip}/easymesh/api.cgi'

        self._session_expired_at = 0

    def _easymesh_statistics_refresh(self):
        def _request_to_easymesh_cgi(body):
            response = self.session.post(self.EASYMESH_CGI, data=body)
            response.raise_for_status()
            if response.text != 'ok':
                raise ServiceCgiExceptions(message=response.text, code=-1)

        body = {'key': 'agent/statistics/refresh'}
        _request_to_easymesh_cgi(body)
        body = {'key': 'station/statistics/refresh'}
        _request_to_easymesh_cgi(body)

    def easymesh_stations(self):
        self.determine_reauth_session_method()
        self._easymesh_statistics_refresh()
        response = self.session.get(self.EASYMESH_CGI + '?key=topology')
        response.raise_for_status()
        data = response.json()

        server_date_header = response.headers.get('Date')
        server_datetime = datetime.strptime(server_date_header, '%a, %d %b %Y %H:%M:%S GMT')
        server_timestamp = server_datetime.timestamp()

        agents = data.get('agent', [])
        controllers = data.get('controller', [])
        stations = data.get('station', [])
        stat = []
        for station in stations:
            stat.append(Station(**station))
        return stat, server_timestamp

    def _request_to_service(self, method: str, params: dict=None) -> dict:
        if method != 'session/login' and method != 'session/update':
            self.determine_reauth_session_method()
        body = {
            'method': method,
        }
        if params:
            body['params'] = params
        response = self.session.post(self.SERVICE_CGI, json=body)
        response.raise_for_status() # 임시방편
        data = response.json()
        err = data.get('error', None)
        if err:
            raise ServiceCgiExceptions(message=err['message'], code=err['code'])
        return data

    @property
    def determine_reauth_session_method(self):
        if self._session_expired_at < time.time():
            return self.session_login
        if self._session_expired_at < time.time() - 100:
            return self.session_update
        return lambda : None

    def session_login(self):
        params = {
            "id": self._username,
            "pw": self._password
        }
        self._request_to_service("session/login", params)
        self.session_update()

    def session_update(self):
        data = self._request_to_service("session/update")
        self._session_expired_at = time.time() + data.get('result', {}).get('timeout', 600)

    def session_info(self):
        data = self._request_to_service("session/info")
        result = data.get('result', {})
        return result

    def product_info(self) -> Router:
        data = self._request_to_service("product/info")
        result = data.get('result', {})
        return Router(**result)

    def system_info(self):
        data = self._request_to_service("system/info")
        result = data.get('result', {})
        return result

    def firmware_version_latest(self) -> str:
        data = self._request_to_service("firmware/version/latest")
        result = data.get('result', '')
        return result

    def firmware_upgrade_prepare(self):
        params = {
            "method": "auto"
        }
        data = self._request_to_service("firmware/upgrade/prepare", params)
        result = data.get('result', '')
        return result

    def firmware_upgrade_online(self):
        data = self._request_to_service("firmware/upgrade/online")
        result = data.get('result', '')
        return result

    def firmware_upgrade_status(self) -> FirmwareUpgradeStatus:
        data = self._request_to_service("firmware/upgrade/status")
        result = data.get('result', {})
        stage = FirmwareUpgradeStatus(result.get('stage', ''))
        return stage

    def easymesh_info(self):
        data = self._request_to_service("easymesh/info")
        result = data.get('result', {})
        return result

    def network_wan_info(self):
        data = self._request_to_service("network/interface/wan1/info")
        result = data.get('result', {})
        return result

    def network_lan_stations(self):
        data = self._request_to_service("network/interface/lan/stations")
        result = data.get('result', {})
        return result

    def connection_info(self):
        data = self._request_to_service("conn/info")
        result = data.get('result', {})
        return result

if __name__ == '__main__':
    api = IPTimeAPIClass("192.168.0.1", "id", "pw")
    while True:
        a, b, c = api.easymesh_stations()
        print(c[0].down_bytes)
        sleep(1.0)
