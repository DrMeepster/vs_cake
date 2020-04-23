#Copyright (c) DrMeepster 2020
#Under MIT License

import json, os, sys, argparse
import regex #different from re, use 'pip install regex'

decomment = regex.compile("/\*.*?\*/ | //[^\n]*?$", regex.M|regex.X|regex.S)

dewhitespace = regex.compile(
        r"(?(DEFINE)"
            + r"(?<op>[!=|&<>+\-/*%^~{}[\]():;,?])"
        + r") (?:\".*?\"|'.*?')(*SKIP)(*F)"
        + r"| \A\s+ | \s+?\Z | (?<sp>(?<=:)\s+?(?=:))"
        + r"| \s+?(?=(?&op)) | (?<=(?&op))\s+ | (?<sp>\s+)",
        regex.M|regex.X|regex.S
    )

findDirectives = regex.compile(
        r"<(?<tag>\w+?)(?<selfend>/)?> (?(selfend)|(?<contents>.*?) </(?P=tag)>)",
        regex.X|regex.S
    )

dirRemove = "remove".casefold()

verbocity = 0

def log(*args, level=1, err=False, **kwargs):
    if err:
        kwargs["file"] = sys.stderr
    if level <= verbocity:
        print(*args, **kwargs)

def findSource(mergeList, mergePath):
    mergeListData = None
    with open(mergeList, "r") as f:
        mergeListData = json.load(f)

    for k in mergeListData:
        mergeListData[k] = [
            os.path.join(mergePath, file)
            for file in mergeListData[k]
        ]

    return mergeListData

def executeDirectives(text):
    offset = 0
    for match in findDirectives.finditer(text):
        if match.group("tag").casefold() == dirRemove:
            text = text[:match.start() - offset] + text[match.end() - offset:]
            
            #later text removals need to be offset by how much text removed here
            offset += len(match.group())
    return text

def _replaceWhitespace(match):
    return " " if match.group("sp") else ""

def minify(file):
    file = executeDirectives(file)
    file = decomment.sub(" ", file)
    file = dewhitespace.sub(_replaceWhitespace, file)
    return file

def makeMerged(files, header=None):
    out = ""

    i = 0
    for file in files:
        i += 1

        if not os.path.exists(file):
            log(f" - Skipping file {os.path.basename(file)}: does not exist ({i}/{len(files)})",
                err=True)
            continue
        
        log(f" - Reading file {os.path.basename(file)} ({i}/{len(files)})")
        with open(file, "r") as f:
                out += f.read()

    out = minify(out)

    if header:
        with open(header, "r") as f:
            out = f.read() + out

    return out

def writeMerged(srcJson, outputPath, header=None, mode="w"):
    i = 0
    for k in srcJson:
        i += 1

        outPath = os.path.join(outputPath, k)

        if mode == "x" and os.path.exists(outPath):
            log(f"Skipping file {k}: already exists ({i}/{len(srcJson)})", err=True)
            continue
        
        log(f"Creating file {k} ({i}/{len(srcJson)})")
        merged = makeMerged(srcJson[k], header)

        try:
            with open(outPath, mode) as f:
                f.write(merged)
        except FileExistsError as e:
            log(e, level=0, err=True)

def makeSingle(filename, rename):
    return {rename if rename else os.path.basename(filename): [filename]}

def main():
    global verbocity
    
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)

    parser.add_argument("-H", "--header")
    parser.add_argument("-x", "--exclusive", action="store_true")

    vArgs = parser.add_mutually_exclusive_group()
    vArgs.add_argument("-v", "--verbose", action="count", default=0)
    vArgs.add_argument("-q", "--quiet", action="count")

    merge = sub.add_parser("merge", aliases=["m"],
        help="Merge and minify files specified in a json file")
    
    merge.set_defaults(cmd="merge")
    merge.add_argument("mergelist", help="Path to a json with the files to merge")
    merge.add_argument("output", nargs="?", default=".", help="Path to output files to")
    merge.add_argument("mergepath", nargs="?", default=".",
        help="Path to look for source files")

    single = sub.add_parser("single", aliases=["s"], help="Minify a single file")
    single.set_defaults(cmd="single")
    single.add_argument("file", help="Path to the file to minify")
    single.add_argument("output", nargs="?", default=".", help="Path to output files to")
    single.add_argument("name", nargs="?", help="New name for the file")

    args = parser.parse_args()

    defaultVerbocity = 1

    if args.quiet:
        verbocity = defaultVerbocity - args.quiet
    else:
        verbocity = defaultVerbocity + args.verbose
        
    src = {
        "single": lambda args: makeSingle(args.file, args.name),
        "merge": lambda args: findSource(args.mergelist, args.mergepath)
    }[args.cmd](args)

    writeMerged(
        src, args.output, args.header,
        "x" if args.exclusive else "w"
    )
    
    log("Done.")

if __name__ == "__main__":
    main()
