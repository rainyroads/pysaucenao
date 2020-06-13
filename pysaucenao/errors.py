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
    """
    TODO: This will probably be renamed in the future, as we know what non-zero status codes generally mean
    """
    pass
