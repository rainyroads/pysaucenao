class SauceNaoException(Exception):
    pass


class ShortLimitReachedException(SauceNaoException):
    pass


class DailyLimitReachedException(SauceNaoException):
    pass


class InvalidOrWrongApiKeyException(SauceNaoException):
    pass


class FileSizeLimitException(SauceNaoException):
    pass


class ImageSizeException(SauceNaoException):
    pass


class InvalidImageException(SauceNaoException):
    pass


class TooManyFailedRequestsException(SauceNaoException):
    pass


class BannedException(SauceNaoException):
    pass


class UnknownStatusCodeException(SauceNaoException):
    pass
