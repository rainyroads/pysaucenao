import asyncio
import logging
from typing import *

from pysaucenao.errors import *

import aiohttp


class SauceNAO:

    API_URL = 'https://saucenao.com/search.php'

    def __init__(self, *, api_key: Optional[str] = None,
                 db_mask: Optional[int] = None,
                 db_mask_disable: Optional[int] = None,
                 db: int = 999,
                 results_limit: int = 6,
                 test_mode: int = 0,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:

        params = dict()
        if api_key:
            params['api_key'] = api_key
        if db_mask:
            params['dbmask'] = str(db_mask)
        if db_mask_disable:
            params['dbmaski'] = str(db_mask_disable)
        params['output_type'] = '2'
        params['testmode'] = str(test_mode)
        params['db'] = str(db)
        params['numres'] = str(results_limit)
        self.params = params

        self._loop = loop
        self._log = logging.getLogger(__name__)

    async def from_url(self, url: str):
        """
        Look up the source of an image on the internet
        """
        params = self.params.copy()
        params['url'] = url
        async with aiohttp.ClientSession(loop=self._loop) as session:
            self._log.debug(f"""Executing SauceNAO API request on URL: {url}""")
            status_code, response = await self._fetch(session, self.API_URL, params)

        self._verify_request(status_code, response)
        return response

    # noinspection PyTypeChecker
    async def from_file(self, fp: str):
        """
        Look up the source of an image on the local filesystem
        """
        params = self.params.copy()
        with open(fp, 'rb') as fh:
            params['file'] = fh
            async with aiohttp.ClientSession(loop=self._loop) as session:
                self._log.debug(f"""Executing SauceNAO API request on local file: {fp}""")
                status_code, response = await self._post(session, self.API_URL, params)

        self._verify_request(status_code, response)
        return response

    def _verify_request(self, status_code: int, data: dict):
        """
        Verify that our request went through successfully
        """
        if status_code == 200:
            header = data['header']
            if header['status'] != 0:
                raise UnknownStatusCodeException(header['message'])
        elif status_code == 429:
            header = data['header']
            if "searches every 30 seconds" in header['message']:
                raise ShortLimitReachedException(header['message'])
            else:
                raise DailyLimitReachedException(header['message'])
        elif status_code == 403:
            raise InvalidOrWrongApiKeyException
        elif status_code == 413:
            raise FileSizeLimitException
        else:
            raise UnknownStatusCodeException

    async def _fetch(self, session: aiohttp.ClientSession, url: str, params: Optional[Mapping[str, str]] = None) -> Tuple[int, dict]:
        async with session.get(url, params=params) as response:
            return response.status, await response.json()

    async def _post(self, session: aiohttp.ClientSession, url: str, params: Optional[Mapping[str, str]] = None) -> Tuple[int, dict]:
        async with session.post(url, data=params) as response:
            return response.status, await response.json()
