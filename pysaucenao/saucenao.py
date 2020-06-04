import asyncio
import logging
from typing import *

import aiohttp

from pysaucenao.containers import *
from pysaucenao.errors import *


class SauceNaoResults:
    """
    SauceNao results container
    """

    def __init__(self, response: dict, min_similarity: typing.Optional[float] = None):
        header, results = response['header'], response['results']
        self.user_id: str               = header['user_id']
        self.account_type: str          = header['account_type']
        self.short_limit: str           = header['short_limit']
        self.long_limit: str            = header['long_limit']
        self.long_remaining: int        = header['long_remaining']
        self.short_remaining: int       = header['short_remaining']
        self.status: int                = header['status']
        self.results_requested: int     = header['results_requested']
        self.search_depth: str          = header['search_depth']
        self.minimum_similarity: float  = header['minimum_similarity']

        self.results: typing.List[GenericSource] = []
        for result in results:
            if min_similarity and float(result['header']['similarity']) < min_similarity:
                continue
            self.results.append(self._process_result(result))

    def _process_result(self, result):
        """
        Parse json response into an applicable container object
        """
        header, data = result['header'], result['data']

        # Pixiv
        if header['index_id'] in (5, 6):
            return PixivSource(header, data)

        # Booru
        if header['index_id'] in [9, 25, 26, 29]:
            return BooruSource(header, data)

        # Video
        if header['index_id'] in [21, 22, 23, 24]:
            return VideoSource(header, data)

        # Manga
        if header['index_id'] in [0, 3, 16, 18, 36, 37]:
            return MangaSource(header, data)

        # Other
        return GenericSource(header, data)

    def __getitem__(self, item):
        return self.results[item]

    def __len__(self):
        return len(self.results)

    def __repr__(self):
        rep = reprlib.Repr()
        rep.maxlist = 4
        return f"<SauceNaoResults(count={len(self.results)}, short_avail={self.short_remaining}, long_avail={self.long_remaining}, results={rep.repr(self.results)})>"


class SauceNao:

    API_URL = 'https://saucenao.com/search.php'

    def __init__(self, *, api_key: Optional[str] = None,
                 db_mask: Optional[int] = None,
                 db_mask_disable: Optional[int] = None,
                 db: int = 999,
                 results_limit: int = 6,
                 min_similarity: float = 65.0,
                 test_mode: int = 0,
                 strict_mode: bool = False,
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
        return SauceNaoResults(response, self._min_similarity)

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
        return SauceNaoResults(response, self._min_similarity)

    def _verify_request(self, status_code: int, data: dict):
        """
        Verify that our request went through successfully
        """
        if status_code == 200:
            header = data['header']
            if header['status'] != 0:
                self._log.warning(f"Non-zero status code returned: {header['status']}")
                # A non-zero status code may just mean some indexes are offline, but we can still get results from
                # those that are up. If strict mode is enabled, we should throw an exception. Otherwise, we return
                # what data we have regardless.
                if self._strict_mode:
                    raise UnknownStatusCodeException(header['status'])
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
