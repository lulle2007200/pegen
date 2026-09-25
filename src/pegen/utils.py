from typing import Protocol
import importlib.util
import io
import sys
import textwrap
from typing import Any, Dict, Final, Optional, Type, cast, TextIO

from pegen.grammar import Grammar
from pegen.grammar_parser import GeneratedParser as GrammarParser
from pegen.python_generator import PythonParserGenerator, default_tokens
from pegen.tokenizer import TokenType
from pegen.parser import BaseParser, PyParser, ParserFactory
from pegen.py_tokenizer import PyTokenType
from pegen.tokenizer import PyTokenizer, TokengenFactory, TokenizerFactory, py_tokengen_factory

def import_file(full_name: str, path: str) -> Any:
    """Import a python module from a path"""

    spec = importlib.util.spec_from_file_location(full_name, path)
    assert spec
    mod = importlib.util.module_from_spec(spec)

    # We assume this is not None and has an exec_module() method.
    # See https://docs.python.org/3/reference/import.html?highlight=exec_module#loading
    loader = cast(Any, spec.loader)
    loader.exec_module(mod)
    return mod


def generate_parser(
    grammar: Grammar, 
    parser_path: Optional[str] = None, 
    parser_name: str = "GeneratedParser",
    parser_class: str = "PyParser",
    parser_args: dict[str, Any] = {},
    tokens: Optional[set[str]] = default_tokens,

) -> Type[BaseParser[TokenType]]:
    # Generate a parser.
    out = io.StringIO()
    genr = PythonParserGenerator(grammar, out, parser_class, parser_args, tokens)
    genr.generate("<string>")

    # Load the generated parser class.
    ns: Dict[str, Any] = {}
    if parser_path:
        with open(parser_path, "w") as f:
            f.write(out.getvalue())
        mod = import_file("py_parser", parser_path)
        return getattr(mod, parser_name)
    else:
        exec(out.getvalue(), ns)
        return ns[parser_name]


def run_parser(file: TextIO, 
               parser_factory: ParserFactory=PyParser,
               tokenizer_factory: TokenizerFactory=PyTokenizer,
               tokengen_factory: TokengenFactory=py_tokengen_factory,
               *, 
               verbose: bool = False):
    tokengen = tokengen_factory(file)
    tokenizer = tokenizer_factory(tokengen, verbose=verbose)
    parser = parser_factory(tokenizer, verbose=verbose)
    result = parser.start()
    if result is None:
        raise parser.make_syntax_error("invalid syntax")
    return result


def parse_string(source: str, 
                 parser_factory: ParserFactory,
                 tokenizer_factory: TokenizerFactory=PyTokenizer,
                 tokengen_factory: TokengenFactory=py_tokengen_factory,
                 *, 
                 dedent: bool=True, 
                 verbose: bool=False) -> Any:
    # Run the parser on a string.
    if dedent:
        source = textwrap.dedent(source)
    file = io.StringIO(source)
    return run_parser(file, parser_factory, tokenizer_factory, tokengen_factory, verbose=verbose)


def make_parser(source: str) -> Type[BaseParser[PyTokenType]]:
    # Combine parse_string() and generate_parser().
    grammar = parse_string(source, GrammarParser)
    return generate_parser(grammar)


def print_memstats() -> bool:
    MiB: Final = 2**20
    try:
        import psutil
    except ImportError:
        return False
    print("Memory stats:")
    process = psutil.Process()
    meminfo = process.memory_info()
    res = {}
    res["rss"] = meminfo.rss / MiB
    res["vms"] = meminfo.vms / MiB
    if sys.platform == "win32":
        res["maxrss"] = meminfo.peak_wset / MiB
    else:
        # See https://stackoverflow.com/questions/938733/total-memory-used-by-python-process
        import resource  # Since it doesn't exist on Windows.

        rusage = resource.getrusage(resource.RUSAGE_SELF)
        if sys.platform == "darwin":
            factor = 1
        else:
            factor = 1024  # Linux
        res["maxrss"] = rusage.ru_maxrss * factor / MiB
    for key, value in res.items():
        print(f"  {key:12.12s}: {value:10.0f} MiB")
    return True
