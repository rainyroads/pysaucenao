import asyncio
import logging
import reprlib
import typing

import aiohttp

from pysaucenao.errors import SauceNaoException

TYPE_GENERIC    = 'generic'
TYPE_PIXIV      = 'pixiv'
TYPE_BOORU      = 'booru'
TYPE_VIDEO      = 'video'
TYPE_ANIME      = 'anime'
TYPE_MANGA      = 'manga'

ACCOUNT_UNREGISTERED    = '0'
ACCOUNT_FREE            = '1'
ACCOUNT_ENHANCED        = '2'

INDEXES = {
    '0' : 'H-Magazines',
    '2' : 'H-Game CG',
    '3' : 'DoujinshiDB',
    '5' : 'Pixiv',
    '6' : 'Pixiv (Historical)',
    '8' : 'Nico Nico Seiga',
    '9' : 'Danbooru',
    '10': 'drawr Images',
    '11': 'Nijie Images',
    '12': 'Yande.re',
    '15': 'Shutterstock',
    '16': 'FAKKU',
    '18': 'H-Misc',
    '19': '2D-Market',
    '20': 'MediBang',
    '21': 'Anime',
    '22': 'H-Anime',
    '23': 'Movies',
    '24': 'Shows',
    '25': 'Gelbooru',
    '26': 'Konachan',
    '27': 'Sankaku Channel',
    '28': 'Anime-Pictures.net',
    '29': 'e621.net',
    '30': 'Idol Complex',
    '31': 'bcy.net Illust',
    '32': 'bcy.net Cosplay',
    '33': 'PortalGraphics.net (Hist)',
    '34': 'deviantArt',
    '35': 'Pawoo.net',
    '36': 'Madokami (Manga)',
    '37': 'MangaDex',
    '38': 'E-Hentai',
}


class SauceNaoResults:
    """
    SauceNao results container
    """

    def __init__(self, response: dict, min_similarity: typing.Optional[float] = None,
                 priority: typing.Optional[typing.List[int]] = None, priority_tolerance: float = 10.0,
                 loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        self._header, self._results = response['header'], response['results']
        self._min_similarity            = min_similarity
        self._priority                  = priority
        self._priority_tolerance        = priority_tolerance
        self._loop                      = loop
        self.user_id: str               = self._header['user_id']
        self.account_type: str          = self._header['account_type']
        self.short_limit: str           = self._header['short_limit']
        self.long_limit: str            = self._header['long_limit']
        self.long_remaining: int        = self._header['long_remaining']
        self.short_remaining: int       = self._header['short_remaining']
        self.status: int                = self._header['status']
        self.results_requested: int     = self._header['results_requested']
        self.search_depth: str          = self._header['search_depth']
        self.minimum_similarity: float  = self._header['minimum_similarity']

        self._sort_results()
        self.results: typing.List[GenericSource] = [self._process_result(r) for r in self._results]

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

        # Anime
        if header['index_id'] in [21, 22]:
            return AnimeSource(header, data, self._loop)

        # Video
        if header['index_id'] in [23, 24]:
            return VideoSource(header, data)

        # Manga
        if header['index_id'] in [0, 3, 16, 18, 36, 37]:
            return MangaSource(header, data)

        # Other
        return GenericSource(header, data)

    def _sort_results(self) -> None:
        """
        Sort SauceNao results by index priority, if desired
        Returns:
            None
        """
        # Filter out results that don't meet the similarity threshold first
        if self._min_similarity:
            self._results = [r for r in self._results if float(r['header']['similarity']) > self._min_similarity]

        # No results to process?
        if not self._results:
            return

        # Get the similarity ranking of the top result as a reference
        tolerance = max([float(r['header']['similarity']) for r in self._results]) - self._priority_tolerance \
            if self._priority_tolerance \
            else None

        # Begin sorting by index priority
        if self._priority:
            priority_index = {}
            extra_results = []
            for index in self._priority:
                priority_index[index] = []

            for result in self._results:
                _index_id = result['header']['index_id']
                _similarity = float(result['header']['similarity'])

                # Make sure the result is within the prioritization tolerance window
                tolerable = True
                if tolerance and _similarity < tolerance:
                    tolerable = False

                if _index_id in self._priority and tolerable:
                    priority_index[_index_id].append(result)
                else:
                    extra_results.append(result)

            # Since we've possibly pulled some things, re-sort the extras now
            extra_results.sort(key=lambda x: float(x['header']['similarity']), reverse=True)

            # Now make sure the priority indexes are sorted
            for _index_id in priority_index.keys():
                priority_index[_index_id].sort(key=lambda x: float(x['header']['similarity']), reverse=True)

            # Time to bring everything back together
            final_results = []
            for index_id, results in priority_index.items():
                final_results += results

            final_results += extra_results
            self._results = final_results

    def __getitem__(self, item):
        return self.results[item]

    def __len__(self):
        return len(self.results)

    def __bool__(self):
        return len(self.results) >= 1

    def __repr__(self):
        rep = reprlib.Repr()
        rep.maxlist = 4
        return f"<SauceNaoResults(count={len(self.results)}, short_avail={self.short_remaining}, long_avail={self.long_remaining}, results={rep.repr(self.results)})>"


class TestResults:
    """
    Container for test query responses.
    """
    def __init__(self, response: dict, error: typing.Optional[SauceNaoException] = None):
        self.error = error
        self.success = not error

        header, results = response.get('header'), response.get('results')
        self.user_id: str               = header.get('user_id')
        self.account_type: str          = str(header.get('account_type'))
        self.short_limit: str           = header.get('short_limit')
        self.long_limit: str            = header.get('long_limit')
        self.long_remaining: int        = header.get('long_remaining')
        self.short_remaining: int       = header.get('short_remaining')
        self.status: int                = header.get('status')

    def __repr__(self):
        account_type = 'unknown'
        if self.account_type == ACCOUNT_UNREGISTERED:
            account_type = 'unregistered'
        if self.account_type == ACCOUNT_FREE:
            account_type = 'free'
        if self.account_type == ACCOUNT_ENHANCED:
            account_type = 'enhanced'

        if self.error:
            return f"<SauceNaoTest(success='{self.success}', account_type='{account_type}', error='{self.error}')>"

        return f"<SauceNaoTest(success='{self.success}', account_type='{account_type}', short_avail={self.short_remaining}, long_avail={self.long_remaining})>"


class GenericSource:
    """
    Basic attributes we should ideally have from any source, but not always
    """

    def __init__(self, header: dict, data: dict):
        self.header = header
        self.data   = data

        self.similarity:    typing.Optional[float] = None
        self.thumbnail:     typing.Optional[str] = None
        self.author_name:   typing.Optional[str] = None
        self.author_url:    typing.Optional[str] = None
        self.title:         typing.Optional[str] = None
        self.url:           typing.Optional[str] = None
        self.urls:          typing.Optional[list] = None
        self.index:         typing.Optional[str] = None  # The name of the index pulled from. See INDEXES above
        self.index_id:      typing.Optional[int] = None
        self.index_name:    typing.Optional[str] = None

        self._parse_data(data)
        self._parse_header(header)

    @property
    def type(self):
        return TYPE_GENERIC

    @property
    def source_url(self):
        """
        Returns the standard URL by default. Booru's may have a link to the original source that replaces this.
        """
        return self.url

    def _parse_header(self, header: dict):
        """
        Parse data in the header field of a response; called during initialization
        """
        # Get the index
        self.index_id = header['index_id']
        if str(self.index_id) in INDEXES:
            self.index = INDEXES[str(self.index_id)]

        self.index_name = header['index_name']
        self.similarity = float(header['similarity'])
        self.thumbnail  = header['thumbnail']

    def _parse_data(self, data: dict):
        """
        Parse data in the data field of a response; called during initialization
        """
        # The "title" can seemingly come from a variety of different fields. These are the ones we know. Adjust as needed
        if 'title' in data:
            self.title = data['title']
        elif 'eng_name' in data:
            self.title = data['eng_name']
        elif 'material' in data:
            self.title = data['material']
        elif 'source' in data:
            self.title = data['source']  # Sometimes this is a URL, sometimes it's a title. ¯\(°_o)/¯

        # Like above, author name can come from multiple fields
        if 'member_name' in data:
            self.author_name = data['member_name']
        elif 'creator' in data:
            # May be multiple creators; we just grab the first in this scenario
            self.author_name = data['creator'][0] if isinstance(data['creator'], list) else data['creator']

        # Same story, different comment line
        if 'author_url' in data:
            self.author_url = data['author_url']
        elif 'pawoo_id' in data and 'ext_urls' in data:
            self.author_url = data['ext_urls'][0]

        # URL to the index page. Booru's may also provide links to the original source, which can be found with source_url
        if 'ext_urls' in data:
            self.url = data['ext_urls'][0]
            self.urls = data['ext_urls']

    def __repr__(self):
        rep = reprlib.Repr()
        return f"<GenericSource(title={rep.repr(self.title)}, author={rep.repr(self.author_name)}, source='{self.index}')>"


class PixivSource(GenericSource):
    """
    The preferred primary source, as Pixiv is the most likely original source for any image
    """

    def __init__(self, header: dict, data: dict):
        super().__init__(header, data)

    @property
    def type(self):
        return TYPE_PIXIV

    def _parse_data(self, data: dict):
        super()._parse_data(data)
        self.author_url = f"https://www.pixiv.net/member.php?id={data['member_id']}"

    def __repr__(self):
        rep = reprlib.Repr()
        return f"<PixivSource(title={rep.repr(self.title)}, author={rep.repr(self.author_name)}, pixiv_id={rep.repr(self.data['member_id'])})>"


class BooruSource(GenericSource):
    """
    Booru related sources. Rarely ever the primary source itself. Will generally only be returned first when the artist
    doesn't exist on Pixiv.
    """

    def __init__(self, header: dict, data: dict):
        super().__init__(header, data)

    @property
    def source_url(self):
        """
        Return the linked source if available
        """
        if 'source' in self.data and self.data['source']:
            return self.data['source']

        return self.url

    @property
    def type(self):
        return TYPE_BOORU

    def _parse_data(self, data: dict):
        super()._parse_data(data)
        self.gelbooru_id = data.get("gelbooru_id")
        self.danbooru_id = data.get("danbooru_id")

        self.characters = data.get("characters")
        if self.characters:
            self.characters = self.characters.replace(', ', ',').split(',')

        self.material = data.get('material')
        if self.material:
            self.material = self.material.replace(', ', ',').split(',')

    def __repr__(self):
        rep = reprlib.Repr()
        return f"<GenericSource(title={rep.repr(self.title)}, author={rep.repr(self.author_name)}, source='{self.index}')>"


class VideoSource(GenericSource):
    """
    Attributes for video sources (i.e. TV series, Movie, etc.)
    Contains unique values such as the episode number and timestamp
    """

    def __init__(self, header: dict, data: dict):
        self.episode:   typing.Optional[str] = None
        self.timestamp: typing.Optional[str] = None
        self.year:      typing.Optional[str] = None

        super().__init__(header, data)

    @property
    def type(self):
        return TYPE_VIDEO

    def _parse_data(self, data: dict):
        super()._parse_data(data)
        if 'part' in data:
            self.episode = data['part']
        if 'est_time' in data:
            self.timestamp = data['est_time']
        if 'year' in data:
            self.year = data['year']

    def __repr__(self):
        rep = reprlib.Repr()
        return f"<VideoSource(title={rep.repr(self.title)}, episode={self.episode}, source='{self.index}')>"


class AnimeSource(VideoSource):
    """
    Attributes specifically for anime and hentai sources
    Contains special methods for obtaining anidb, anilist, mal and kitsu ID's
    """

    def __init__(self, header: dict, data: dict, loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        self._ids = None
        self._loop = loop
        self._log = logging.getLogger(__name__)

        super().__init__(header, data)

    @property
    def type(self):
        return TYPE_ANIME

    async def load_ids(self) -> typing.Dict[str, int]:
        """
        Load and return a list of mapped source ID's
        This needs to be explicitly called before utilizing any of the other class helper properties
        Returns:
            typing.Dict[str, int]
        """
        if self._ids is not None:
            return self._ids

        async with aiohttp.ClientSession(loop=self._loop, raise_for_status=True) as session:
            try:
                response = await session.get(f"https://relations.yuna.moe/api/ids?source=anidb&id={self.data.get('anidb_aid')}")
                if response.status == 204:
                    self._log.info("yuna.moe lookup failed for this anime source")
                else:
                    self._ids = await response.json()
                    return self._ids
            except aiohttp.ClientResponseError as error:
                self._log.error(f'yuna.moe server is returning a {error.status} error code')
            except aiohttp.ClientError:
                self._log.error('yuna.moe server appears to be down or is not responding to our requests')

        self._ids = {}

    # ID getters
    @property
    def anidb_id(self):
        return self.data.get('anidb_aid')

    @property
    def anilist_id(self):
        self._id_check()
        return self._ids.get('anilist')

    @property
    def mal_id(self):
        self._id_check()
        return self._ids.get('myanimelist')

    @property
    def kitsu_id(self):
        self._id_check()
        return self._ids.get('kitsu')

    # URL getters
    @property
    def anidb_url(self):
        return f"https://anidb.net/anime/{self.anidb_id}"

    @property
    def anilist_url(self):
        if not self._id_check('anilist'):
            return None

        return f"https://anilist.co/anime/{self.anilist_id}"

    @property
    def mal_url(self):
        if not self._id_check('myanimelist'):
            return None

        return f"https://myanimelist.net/anime/{self.mal_id}"

    @property
    def kitsu_url(self):
        if not self._id_check('kitsu'):
            return None

        return f"https://kitsu.io/anime/{self.kitsu_id}"

    def _id_check(self, index: typing.Optional[str] = None):
        if self._ids is None:
            raise IndexError('You must run the load_ids() method before accessing this property')

        if index:
            if index in self._ids and self._ids[index]:
                return True

            return False

    def __repr__(self):
        rep = reprlib.Repr()
        return f"<AnimeSource(title={rep.repr(self.title)}, episode={self.episode}, source='{self.index}', ids_loaded='{self._ids is not None}')>"


class MangaSource(GenericSource):

    def __init__(self, header: dict, data: dict):

        self.chapter:       typing.Optional[str] = None
        super().__init__(header, data)

    @property
    def type(self):
        return TYPE_MANGA

    def _parse_data(self, data: dict):
        super()._parse_data(data)
        if 'part' in data:
            self.chapter = data['part']

        if 'author' in data:
            self.author_name = data['author']
        elif 'creator' in data:
            self.author_name = data['creator']

    def __repr__(self):
        rep = reprlib.Repr()
        return f"<MangaSource(title={rep.repr(self.title)}, author={self.author_name} chapter={self.chapter}, source='{self.index}')>"
