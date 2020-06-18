import asyncio
import logging
from typing import *

import aiohttp

from pysaucenao.containers import *
from pysaucenao.errors import *


class SauceNao:

    API_URL = 'https://saucenao.com/search.php'

    def __init__(self, *, api_key: Optional[str] = None,
                 db_mask: Optional[int] = None,
                 db_mask_disable: Optional[int] = None,
                 db: int = 999,
                 results_limit: int = 6,
                 min_similarity: float = 50.0,
                 test_mode: int = 0,
                 strict_mode: bool = True,
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

        self._min_similarity = min_similarity
        self._strict_mode = strict_mode
        self._loop = loop
        self._log = logging.getLogger(__name__)

    async def from_url(self, url: str) -> SauceNaoResults:
        """
        Look up the source of an image on the internet
        Args:
            url (str): Web URL to an image

        Returns:
            SauceNaoResults
        """
        params = self.params.copy()
        params['url'] = url
        async with aiohttp.ClientSession(loop=self._loop) as session:
            self._log.debug(f"""Executing SauceNAO API request on URL: {url}""")
            status_code, response = await self._fetch(session, self.API_URL, params)

        self._verify_request(status_code, response)
        return SauceNaoResults(response, self._min_similarity)

    # noinspection PyTypeChecker
    async def from_file(self, fp: str) -> SauceNaoResults:
        """
        Look up the source of an image on the local filesystem
        Args:
            fp (str): Path to the file to open

        Returns:
            SauceNaoResults
        """
        params = self.params.copy()
        with open(fp, 'rb') as fh:
            params['file'] = fh
            async with aiohttp.ClientSession(loop=self._loop) as session:
                self._log.debug(f"""Executing SauceNAO API request on local file: {fp}""")
                status_code, response = await self._post(session, self.API_URL, params)

        self._verify_request(status_code, response)
        return SauceNaoResults(response, self._min_similarity)

    async def test(self) -> TestResults:
        """
        Executes a test query and returns account information for the provided API key
        Returns:
            TestResults
        """
        params = self.params.copy()
        params['testmode'] = '1'
        params['numres'] = '1'
        params['url'] = 'http://saucenao.com/images/static/banner.gif'

        async with aiohttp.ClientSession(loop=self._loop) as session:
            self._log.debug('Executing a test SauceNao API request')
            status_code, response = await self._fetch(session, self.API_URL, params)

        # For test queries, we just grab and store the exception on failure
        error = None
        try:
            self._verify_request(status_code, response)
        except SauceNaoException as _error:
            error = _error

        return TestResults(response, error)

    def _verify_request(self, status_code: int, data: dict) -> None:
        """
        Verify that our request went through successfully
        Returns:
            None
        """
        if status_code == 200:
            header = data['header']
            # Technically, an invalid API key will still be accepted and can return results. We will just be processing
            # this as a guest query. If we have strict mode enabled, we should throw an exception anyways.
            if self._strict_mode and (self.params.get('api_key') and not header['account_type']):
                raise InvalidOrWrongApiKeyException('The provided API key does not exist')

            if header['status'] != 0:
                # Generic error, may indicate some databases are down or there's an account issue. May not be critical.
                if header['status'] == 1:
                    self._log.warning(header.get('message'))
                    if self._strict_mode:
                        raise UnknownStatusCodeException(header.get('status'))

                # Account does not have API access. Likely means you've been banned. Contact SauceNao for support.
                if header['status'] == -1:
                    self._log.error(header.get('message'))
                    raise BannedException(header.get('message'))

                # These status codes means either an invalid file was uploaded or SauceNao could not download a remote image
                if header['status'] in (-3, -4, -6):
                    self._log.warning(header.get('message'))
                    raise InvalidImageException(header.get('message'))

                # Generally this should be caught via a 413 error, but just in-case
                if header['status'] == -5:
                    self._log.warning(header.get('message'))
                    raise FileSizeLimitException(header.get('message'))

                if header['status'] < 0:
                    self._log.warning(f"Non-zero status code returned: {header.get('status')}")
                    # A positive non-zero status code may just mean some indexes are offline, but we can still get results
                    # from those that are up. A negative status code means something more serious went wrong.
                    if self._strict_mode or 'results' not in data:
                        raise UnknownStatusCodeException(header.get('status'))
        elif status_code == 429:
            header = data['header']
            if header.get('status') == -2:
                raise TooManyFailedRequestsException(header.get('message'))

            if "searches every 30 seconds" in header.get('message'):
                raise ShortLimitReachedException(header.get('message'))
            else:
                raise DailyLimitReachedException(header.get('message'))
        elif status_code == 403:
            raise InvalidOrWrongApiKeyException
        elif status_code == 413:
            raise FileSizeLimitException
        else:
            raise UnknownStatusCodeException(f"HTTP {status_code}")

    async def _fetch(self, session: aiohttp.ClientSession, url: str, params: Optional[Mapping[str, str]] = None) -> Tuple[int, dict]:
        async with session.get(url, params=params) as response:
            return response.status, await response.json()

    async def _post(self, session: aiohttp.ClientSession, url: str, params: Optional[Mapping[str, str]] = None) -> Tuple[int, dict]:
        async with session.post(url, data=params) as response:
            return response.status, await response.json()
