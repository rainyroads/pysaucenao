# PySauceNao
![GitHub](https://img.shields.io/github/license/FujiMakoto/pysaucenao) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/fujimakoto/pysaucenao)

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
                 min_similarity: float = 65.0,
                 test_mode: int = 0,
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
results = sauce.from_url('https://i.imgur.com/oVPWy7f.png')

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
results = sauce.from_url('https://i.imgur.com/1M8MhB0.png')

if isinstance(results[0], VideoSource):
    results[0].episode    # '1'
    results[0].year       # '2017'
    results[0].timestamp  # '00:07:53 / 00:23:40'
```

MangaSource search results, similarly, provide an additional `chapter` property.

## Registering for an API key
If you are performing lots of API queries, you will eventually need to sign up and register for an API key (and possibly upgrade your account for very large request volumes)

You can register for an account on [SauceNAO's website](https://saucenao.com/user.php)

## Error handling
The SauceNao class will throw an exception if any of the following occur:
* You have exceeded your 30-second search query limit (ShortLimitReachedException)
* You have exceeded your 24-hour search query limit (DailyLimitReachedException)
* You attempted to upload a file larger than SauceNAO allows (FileSizeLimitException)
* You provided an invalid API key (InvalidOrWrongApiKeyException)
* Any other unknown error occurred / service may be down (UnknownStatusCodeException)

All of these exceptions extend a base SauceNaoException class for easy catching and handling.
