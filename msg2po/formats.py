# File format definitions for supported game translation formats.
# Pure data, no logic or dependencies on other msg2po modules.

from typing import TypedDict


class LineFormat(TypedDict, total=False):
    default: str
    context: str
    female: str


class FileFormat(TypedDict, total=False):
    pattern: str
    dotall: bool
    index: int
    value: int
    context: int
    female: int
    comment: str
    line_format: LineFormat
    forbidden_characters: list[str]


# Extensions recognized by file2po, po2file, etc.
VALID_EXTENSIONS = ["msg", "txt", "sve", "tra"]

# Supported file formats.
# pattern is used to parse original files.
# line_format to write to translated files.
# index, value, context, female - order of these tokens in pattern.
# dotall - whether file entries are multiline.
FILE_FORMAT: dict[str, FileFormat] = {
    "msg": {
        "pattern": r"{(\d+)}{([^}]*)}{([^}]*)}",
        "dotall": True,
        "index": 0,
        "value": 2,
        "context": 1,
        "line_format": {
            "default": "{{{index}}}{{}}{{{value}}}\n",
            "context": "{{{index}}}{{{context}}}{{{value}}}\n",
            "female": "separate",
        },
        "forbidden_characters": ["{", "}"],
    },
    "sve": {
        "pattern": r"(\d+):(.*)",
        "dotall": False,
        "index": 0,
        "value": 1,
        "line_format": {
            "default": "{index}:{value}\n",
            "female": "separate",
        },
        "forbidden_characters": [],
    },
    "txt": {
        "pattern": r"(\d+):(.*)",
        "dotall": False,
        "index": 0,
        "value": 1,
        "comment": "indexed_txt",
        "line_format": {
            "default": "{index}:{value}\n",
            "female": "separate",
        },
        "forbidden_characters": [],
    },
    "tra": {
        "pattern": r"@(\d+)\s*?=\s*?~([^~]*?)~(?:\s)?(?:\[([^]]*)\])?(?:~([^~]*)~)?",
        "dotall": True,
        "index": 0,
        "value": 1,
        "context": 2,
        "female": 3,
        "line_format": {
            "default": "@{index} = ~{value}~\n",
            "context": "@{index} = ~{value}~ [{context}]\n",
            "female": "@{index} = ~{value}~ ~{female}~\n",
        },
        "forbidden_characters": [],
    },
}
