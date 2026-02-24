from enum import Enum
from typing import Any, Optional, List

_POWER_ALIASES = {
    "EGMANY": "GERMANY",
    "GERMAN": "GERMANY",
    "UK": "ENGLAND",
    "BRIT": "ENGLAND",
    "Germany": "GERMANY",
    "England": "ENGLAND",
    "France": "FRANCE",
    "Italy": "ITALY",
    "Russia": "RUSSIA",
    "Austria": "AUSTRIA",
    "Turkey": "TURKEY",
}

POWERS_ORDER: List[str] = [
    "AUSTRIA", "ENGLAND", "FRANCE", "GERMANY",
    "ITALY", "RUSSIA", "TURKEY",
]


class PowerEnum(str, Enum):
    AUSTRIA = "AUSTRIA"
    ENGLAND = "ENGLAND"
    FRANCE = "FRANCE"
    GERMANY = "GERMANY"
    ITALY = "ITALY"
    RUSSIA = "RUSSIA"
    TURKEY = "TURKEY"

    @classmethod
    def _missing_(cls, value: Any) -> Optional["Enum"]:
        if isinstance(value, str):
            normalized = value.upper().strip()
            normalized = _POWER_ALIASES.get(normalized, normalized)
            member = cls._value2member_map_.get(normalized)
            if member is not None:
                return member
        return super()._missing_(value)
