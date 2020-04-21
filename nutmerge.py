#Copyright (c) DrMeepster 2020
#Under MIT License

import json, os, sys, argparse, fnmatch
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

def processFile(file):
    file = executeDirectives(file)
    file = decomment.sub(" ", file)
    file = dewhitespace.sub(_replaceWhitespace, file)
    return file

def makeMerged(files, header=None):
    out = ""

    i = 0
    for file in files:
        i += 1
        log(f" - Reading file {os.path.basename(file)} ({i}/{len(files)})")
        try:
            with open(file, "r") as f:
                out += f.read()
        except FileNotFoundError as e:
            log(e, level=0, err=True)

    out = processFile(out)

    if header:
        with open(header, "r") as f:
            out = f.read() + out

    return out

def writeMerged(srcJson, outputPath, file="*", header=None, mode="w"):
    i = 0
    for k in srcJson:
        i += 1
        if not fnmatch.fnmatch(k, file):
            log(f"Skipping file {k} ({i}/{len(srcJson)})")
            continue

        log(f"Creating file {k} ({i}/{len(srcJson)})")
        merged = makeMerged(srcJson[k], header)

        try:
            with open(os.path.join(outputPath, k), mode) as f:
                f.write(merged)
        except FileExistsError as e:
            log(e, level=0, err=True)

def makeSingle(filename):
    return {os.path.basename(filename): filename}

def main():
    global verbocity
    
    parser = argparse.ArgumentParser()

    parser.add_argument("mergelist")
    parser.add_argument("output", nargs="?", default="")
    parser.add_argument("mergepath", nargs="?", default="")
    parser.add_argument("mergefile", nargs="?", default="*")
    
    parser.add_argument("-H", "--header")
    parser.add_argument("-s", "--single", action="store_true")
    parser.add_argument("-x", "--exclusive", action="store_true")

    vArgs = parser.add_mutually_exclusive_group()
    vArgs.add_argument("-v", "--verbose", action="count")
    vArgs.add_argument("-q", "--quiet", action="count")

    #args = parser.parse_args()
    #args = parser.parse_args(["-h"])
    args = parser.parse_args(["-vv","-H","header.txt","merge_list.json","build","vs_library"])

    defaultVerbocity = 1

    if args.verbose:
        verbocity = defaultVerbocity + args.verbose
    elif args.quiet:
        verbocity = defaultVerbocity - args.quiet
    else:
        verbocity = defaultVerbocity

    writeMerged(findSource(args.mergelist, args.mergepath),
                "build", args.mergefile, args.header, "x" if args.exclusive else "w")
    
    #print(makeMerged([r"vs_library\vs_math2.nut"]))
    log("Done.")

if __name__ == "__main__":
    main()
    
#files = findSource(mergeList, mergePath)
#print(makeMerged(files["vs_library"], headerFile))
