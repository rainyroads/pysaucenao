import reprlib
import typing

from pysaucenao.errors import SauceNaoException

TYPE_GENERIC    = 'generic'
TYPE_PIXIV      = 'pixiv'
TYPE_BOORU      = 'booru'
TYPE_VIDEO      = 'video'
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
