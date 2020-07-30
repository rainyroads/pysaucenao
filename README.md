# PySauceNao
[![GitHub](https://img.shields.io/github/license/FujiMakoto/pysaucenao)](https://github.com/FujiMakoto/pysaucenao/blob/master/LICENSE) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pysaucenao)](https://pypi.org/project/pysaucenao/) [![PyPI](https://img.shields.io/pypi/v/pysaucenao)](https://pypi.org/project/pysaucenao/) [![GitHub commits since latest release (by date)](https://img.shields.io/github/commits-since/fujimakoto/pysaucenao/latest)](https://github.com/FujiMakoto/pysaucenao/releases)

PySauceNao is an unofficial asynchronous library for the [SauceNao](https://saucenao.com/) API. It supports lookups via URL or from the local filesystem.

# Installation
This library requires [Python 3.6](https://www.python.org) or above.

You can install the library through pip as follows,
```shell script
pip install pysaucenao
```

## Usage
```python
from pysaucenao import SauceNao
sauce = SauceNao(self, *, api_key: Optional[str] = None,
                 db_mask: Optional[int] = None,
                 db_mask_disable: Optional[int] = None,
                 db: int = 999,
                 results_limit: int = 6,
                 min_similarity: float = 50.0,
                 test_mode: int = 0,
                 strict_mode: bool = True,
                 loop: Optional[asyncio.AbstractEventLoop] = None)

# results = await sauce.from_file('/path/to/image.png')
results = await sauce.from_url('https://i.imgur.com/QaKpV3s.png')
repr(results)
```
```
<SauceNaoResults(count=2, short_avail=3, long_avail=87, results=[<GenericSourc... Nico Seiga')>, <GenericSourc...e='Danbooru')>])>
```

The library attempts to provide a developer friendly container format for all results. Meaning, no matter if SauceNao returns a Pixiv source result or a more obscure source, you'll be able to easily pull the title, author URL and other useful information.

```python
from pysaucenao import SauceNao, PixivSource
sauce = SauceNao()
results = await sauce.from_url('https://i.imgur.com/oVPWy7f.png')

len(results)  # 4

# Find out how many API request limits you have remaining after a search query
results.short_remaining  # 3 (per 30 seconds limit)
results.long_remaining   # 86 (per day limit)

# You can determine whether the search result is a Pixiv, Booru, Video or Other/Generic result by the type property or type checking
results[0].type  # pixiv
isinstance(results[0], PixivSource)  # True

results[0].similarity     # 96.07
results[0].thumbnail      # Returns a temporary signed URL; not suitable for permanent hotlinking
results[0].title          # なでなでするにゃ
results[0].author_name    # おーじ茶＠3日目I-03b
results[0].author_url     # https://www.pixiv.net/member.php?id=122233
results[0].url            # https://www.pixiv.net/member_illust.php?mode=medium&illust_id=66106354
results[0].source_url     # Same as url for Pixiv results, but returns the linked original source URL for Booru entries
results[0].index          # Pixiv
```

Video search results provide three additional properties containing the episode number, estimated timestamp, and release year
```python
from pysaucenao import SauceNao, VideoSource
sauce = SauceNao()
results = await sauce.from_url('https://i.imgur.com/1M8MhB0.png')

if isinstance(results[0], VideoSource):
    results[0].episode    # '1'
    results[0].year       # '2017'
    results[0].timestamp  # '00:07:53 / 00:23:40'
```

MangaSource search results, similarly, provide an additional `chapter` property.

### Advanced usage

#### Additional source URL's
Thanks to [yuna.moe](https://github.com/BeeeQueue/arm-server), pysaucenao is no longer limited to just AniDB source URL's for anime results as of v1.3

To utilize this new feature, you should first verify you are working with an Anime source.

Once you have done that, you will need to preload the ID map by running the **load_ids** method.

If you attempt to access any of the additional AnimeSource properties without first doing this, you will get an IndexError.
```python
from pysaucenao import SauceNao, AnimeSource
sauce = SauceNao()
results = await sauce.from_url('https://i.imgur.com/poAmgY0.png')

if isinstance(results[0], AnimeSource):
    await results[0].load_ids()
```
This will map the AniDB ID SauceNao returns with several other anime databases,
```python
results[0].title        # Made in Abyss
results[0].anilist_id   # 97986
results[0].anilist_url  # https://anilist.co/anime/97986
results[0].mal_url      # https://myanimelist.net/anime/34599
results[0].kitsu_url    # https://kitsu.io/anime/13273
```

#### Priority
If you want to prioritize certain types of results, you can do so using the `priority` setting as of v1.2

The most useful case for this is to prioritize anime results, preventing anime screencaps hosted on DeviantArt and other indexes some taking priority.

To use this in your own code, just initialize SauceNao like so,
```python
sauce = SauceNao(priority=[21, 22])
```
As long as the anime search results are reasonably close to the next best match SauceNao returns, this will make sure the library always returns the anime result first, and ideally never a reposted screen-grab.

If you need to prioritize other indexes, you can find a list of ID's here:
https://github.com/FujiMakoto/pysaucenao/blob/master/pysaucenao/containers.py#L16-L50

## Registering for an API key
If you are performing lots of API queries, you will eventually need to sign up and register for an API key (and possibly upgrade your account for very large request volumes)

You can register for an account on [SauceNAO's website](https://saucenao.com/user.php)

## Error handling
The SauceNao class will throw an exception if any of the following occur:
* You have exceeded your 30-second search query limit (ShortLimitReachedException)
* You have exceeded your 24-hour search query limit (DailyLimitReachedException)
* You attempted to upload a file larger than SauceNAO allows (FileSizeLimitException)
* You provided an invalid API key (InvalidOrWrongApiKeyException)
* The image was too small for use (ImageSizeException)
* Either the URL or file provided was not a valid image (InvalidImageException)
* Too many failed requests made; try again later (TooManyFailedRequestsException)
* Your account does not have API access; contact SauceNao support (BannedException)
* Any other unknown error occurred / service may be down (UnknownStatusCodeException)

All of these exceptions extend a base SauceNaoException class for easy catching and handling.
