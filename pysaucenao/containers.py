import typing

TYPE_GENERIC    = 'generic'
TYPE_PIXIV      = 'pixiv'
TYPE_BOORU      = 'booru'
TYPE_VIDEO      = 'video'


class GenericSource:
    """
    Basic attributes we should ideally have from any source, but not always
    Documentation is a bit lacking so we have to assume and adjust based on real-world tests
    """
    author_name:    typing.Optional[str]
    author_photo:   typing.Optional[str]
    author_url:     typing.Optional[str]
    title:          typing.Optional[str]
    url:            typing.Optional[str]

    def __init__(self, header: dict, data: dict):
        self.header = header
        self.data   = data

    @property
    def type(self):
        return TYPE_GENERIC


class PixivSource(GenericSource):
    """
    The preferred primary source, as Pixiv is the most likely original source for any image
    """

    def __init__(self, header: dict, data: dict):
        super().__init__(header, data)

    @property
    def type(self):
        return TYPE_PIXIV


class BooruSource(GenericSource):
    """
    Booru related sources. Rarely ever the primary source itself. Will generally only be returned first when the artist
    doesn't exist on Pixiv.
    """

    def __init__(self, header: dict, data: dict):
        super().__init__(header, data)

    @property
    def type(self):
        return TYPE_BOORU


class VideoSource(GenericSource):
    # Attributes for video sources (i.e. TV series, Movie, etc.)
    # Contains unique values such as the episode number and timestamp

    def __init__(self, header: dict, data: dict):
        super().__init__(header, data)

    @property
    def type(self):
        return TYPE_VIDEO
