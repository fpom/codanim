import argparse, pathlib, importlib, sys
from . import lang as _lang

languages = {}

for path in pathlib.Path(_lang.__file__).parent.glob("*.py") :
    module_name = path.with_suffix("").name
    if module_name == "__init__" :
        continue
    module = importlib.import_module(f".lang.{module_name}", package="codanim")
    languages[module_name.lower()] = module

class ListLang (argparse.Action) :
    def __call__ (self, parser, *l, **k) :
        print("Supported languages:")
        width = max(len(l) for l in languages) + 4
        for lang, module in sorted(languages.items()) :
            print((" - {lang:<%s} {help}" % width).format(lang=lang,
                                                          help=module.translate.__doc__))
        parser.exit(0)

parser = argparse.ArgumentParser(
    prog="codanim",
    description="parse code and generate Python stub suitable for codanim")

parser.add_argument("-l", "--lang",
                    default=None,
                    help="language to be parsed (default: guess from file name)")
parser.add_argument("-L", "--list-lang", nargs=0,
                    action=ListLang,
                    help="list supported languages")
parser.add_argument("-o", "--output", type=argparse.FileType("w"),
                    default=sys.stdout,
                    help="output file")
parser.add_argument("SOURCE", type=argparse.FileType("r"),
                    help="source file")
args = parser.parse_args()

if args.lang is None :
    args.lang = args.SOURCE.name.rsplit(".")[-1]

args.lang = args.lang.lower()

if args.lang not in languages :
    parser.error("unsupported language: %r" % args.lang)

translate = languages[args.lang].translate

args.output.write(repr(translate(args.SOURCE.read())) + "\n")
