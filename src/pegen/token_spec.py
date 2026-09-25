from types import ModuleType
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Optional
from pegen import parser
from pegen import tokenizer
from pegen.parser import BaseParser
from pegen.tokenizer import Tokenizer
import re
import keyword
import tomllib

@dataclass(frozen=True)
class TokenDef:
    maps_to: Optional[str] = None
    calls: Optional[str] = None

@dataclass
class TokenSpec:
    tokens: dict[str, TokenDef] = field(default_factory=dict)
    exhaustive: bool = True
    parser_meta: dict[str, Any] = field(default_factory=dict)
    base_parser: str = "PyParser"
    base_parser_mod: str = ""
    keyword_re: str = r"[a-zA-Z_]\w*\Z"

    def check_class(self, 
                    default_module: ModuleType, 
                    base_class: type, 
                    option_name: str, 
                    class_ref: str) -> tuple[str, str]:
        class_ref = class_ref.strip()
        class_ref_stripped = class_ref.lstrip(".")
        parts = class_ref_stripped.split(".")

        if not parts or not all(p.isidentifier() and not keyword.iskeyword(p) for p in parts):
            raise ValueError(f"{option_name} {class_ref!r} is not a valid parser class path.")

        dots = len(class_ref) - len(class_ref.lstrip("."))
        prefix = "." * dots + ".".join(parts[:-2])
        class_name = parts[-1]

        if not isinstance(self.parser_meta, dict):
            raise ValueError("bases_parser_kwargs must be a dict.")

        if not isinstance(self.exhaustive, bool):
            raise ValueError("exhustive must be true or false.")

        if not prefix:
            module_name = default_module.__name__
            cls = getattr(default_module, class_name, None)
            if not cls or not issubclass(cls, base_class):
                raise ValueError(f"{option_name} {class_ref!r} not found in pegen.parser.")
        else:
            module_name = prefix

        return module_name, class_name


    def __post_init__(self) -> None:
        self.base_parser_mod, self.base_parser = self.check_class(parser, BaseParser, "Parser", self.base_parser)

        try:
            re.compile(self.keyword_re)
        except re.error:
            raise ValueError(f"{self.keyword_re!r} is not a valid regular expression.")

        tok_re = re.compile(r"[a-zA-Z][a-zA-Z0-9-_]*")
        for name, spec in self.tokens.items():
            if not tok_re.match(name):
                raise ValueError(f"{name!r} is not a valid token name.")
            if spec.maps_to and (not spec.maps_to.isidentifier() or keyword.iskeyword(spec.maps_to)):
                raise ValueError(f"{spec.maps_to} is invalid. maps_to must be a valid indentifier.")


    @classmethod
    def from_file(cls, file: BinaryIO) -> TokenSpec:
        data: dict[str, Any] = tomllib.load(file)

        scalar_fields = set(("exhaustive", "base_parser", "parser_meta", "keyword_re"))
        known_fields = scalar_fields | {"tokens"}

        unknown = set(data) - known_fields
        if unknown:
            raise ValueError(f"Unknown top-level key(s) in token spec: {sorted(unknown)}.")

        args: dict[str, Any] = {k: data[k] for k in scalar_fields if k in data}

        raw_tokens: Any = data.get("tokens", {})
        if not isinstance(raw_tokens, dict):
            raise ValueError("Expected tokens to be a table")
        tokens: dict[str, TokenDef] = {}
        for name, value in raw_tokens.items():
            try:
                tokens[name] = TokenDef(**value)
            except TypeError as exc:
                raise ValueError(f"Invalid definition for token {name!r}: {exc}") from exc
        args["tokens"] = tokens

        return cls(**args)

    @classmethod
    def from_path(cls, path: Path) -> TokenSpec:
        with open(path, "rb") as f:
            return cls.from_file(f)
