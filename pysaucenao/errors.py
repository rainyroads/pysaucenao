class SauceNAOException(Exception):
    pass


class ShortLimitReachedException(SauceNAOException):
    pass


class DailyLimitReachedException(SauceNAOException):
    pass


class InvalidOrWrongApiKeyException(SauceNAOException):
    pass


class FileSizeLimitException(SauceNAOException):
    pass


class UnknownStatusCodeException(SauceNAOException):
    pass
