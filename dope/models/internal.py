class FileSuffix(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info):  # note the additional '_info' parameter
        if not isinstance(v, str):
            raise TypeError("string required")
        if not v.startswith("."):
            v = "." + v
        return v.lower()
