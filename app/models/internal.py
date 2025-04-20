class FileSuffix(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info):  # note the additional 'info' parameter
        if not isinstance(v, str):
            raise TypeError("string required")
        if not v.startswith("."):
            v = "." + v
        return v.lower()
