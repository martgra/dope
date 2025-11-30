from dope.exceptions import InvalidSuffixError


class FileSuffix(str):
    """File suffix validation class."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):  # noqa: D102
        if not isinstance(v, str):
            raise InvalidSuffixError(str(v), "Suffix must be a string")
        if not v.startswith("."):
            v = "." + v
        return v.lower()
