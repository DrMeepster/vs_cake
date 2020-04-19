#Copyright (c) DrMeepster 2020
#Under MIT License

import json, os, sys, argparse, fnmatch
import regex #different from re, use 'pip install regex'

cleanup = regex.compile(
        r"(?(DEFINE)"
            + r"(?<op>[!=|&<>+\-/*%^~{}[\]():;,?])"
            + r"(?<tgt>(?:/\*.*?\*/|//[^\n]*?(?:\n|\Z)|\s))"
        + r") (?:\".*?\"|'.*?')(*SKIP)(*F)"
        + r"| \A(?&tgt)+ | (?&tgt)+?\Z | (?<sp>(?<=:)(?&tgt)+?(?=:))"
        + r"| (?&tgt)+?(?=(?&op)) | (?<=(?&op))(?&tgt)+ | (?<sp>(?&tgt)+)",
        regex.M|regex.X|regex.S
    )

findDirectives = regex.compile(
        r"<(?<tag>\w+?)(?<selfend>/)?> (?(selfend)|(?<contents>.*?) </(?P=tag)>)",
        regex.X|regex.S
    )

dirRemove = "remove".casefold()

verbocity = 2

def log(*args, level=1, **kwargs):
    if level >= verbocity:
        print(*args, **kwargs)

def findSource(mergeList, mergePath):
    mergeListData = None
    with open(mergeList, "r") as f:
        mergeListData = json.load(f)

    for k in mergeListData:
        mergeListData[k] = [
            os.path.join(mergePath, file)
            for file in mergeListData[k]
            if os.path.exists(os.path.join(mergePath, file))
        ]

    return mergeListData

def executeDirectives(text):
    for match in findDirectives.finditer(text):
        if match.group("tag").casefold() == dirRemove:
            text = text[:match.start()] + text[match.end():]

    return text

def _replaceWhitespace(match):
    return " " if match.group("sp") else ""

def processFile(file):
    out = None

    with open(file, "r") as f:
        out = f.read()

    out = executeDirectives(out)
    out = cleanup.sub(_replaceWhitespace, out)
    return out

def makeMerged(files, header=None):
    out = ""

    if header:
        with open(header, "r") as f:
            out = f.read()
    
    for file in files:
        out += processFile(file)

    return out

def writeMerged(srcJson, outputPath, file="*", header=None, mode="w+"):
    i = 0
    for k in srcJson:
        i += 1
        if not fnmatch.fnmatch(k, file):
            log(f"Skipping file {k} ({i}/{len(srcJson)})")
            continue

        log(f"Creating file {k} ({i}/{len(srcJson)})")
        merged = makeMerged(srcJson[k], header)
        
        with open(os.path.join(outputPath, k), mode) as f:
            f.write(merged)

def makeSingle(filename):
    return {os.path.basename(filename): filename}

if __name__ == "__main__":
    #parser = argparse.ArgumentParser()

    #parser.add_argument("mergelist")
    #parser.add_argument("mergefile", nargs="?", default="*")
    #parser.add_argument("-H", "--header")
    #parser.add_argument("-s", "--single", action="store_true")
    #parser.add_argument("-x", "--exclusive", action="store_true")

    #args = parser.parse_args()
    
    mergeList = "merge_list.json"
    mergeFile = "*"
    mergePath = "vs_library"
    headerFile = "header.txt"
    verbocity = 1

    #writeMerged(findSource(mergeList, mergePath), "build", file=mergeFile, header=headerFile)
    print(makeMerged([r"vs_library\vs_math2.nut"]))
    log("Done.")
    

#files = findSource(mergeList, mergePath)
#print(makeMerged(files["vs_library"], headerFile))
