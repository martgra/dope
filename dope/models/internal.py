class FileSuffix(str):
    """File suffix validation class."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):  # noqa: D102
        if not isinstance(v, str):
            raise TypeError("string required")
        if not v.startswith("."):
            v = "." + v
        return v.lower()
