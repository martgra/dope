from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from dope.exceptions import InvalidSuffixError


class FileSuffix(str):
    """File suffix validation class."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Get Pydantic core schema for validation."""
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, v: str) -> str:
        """Validate and normalize file suffix."""
        if not isinstance(v, str):
            raise InvalidSuffixError(str(v), "Suffix must be a string")
        if not v.startswith("."):
            v = "." + v
        return v.lower()
