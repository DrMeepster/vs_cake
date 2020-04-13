import json, os, sys, regex, argparse
#different from re, use `pip install regex`

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    mergeList = "merge_list.json"
    mergePath = "vs_library"
    headerFile = "header.txt"
    extension = ".nut"

    args = parser.parse_args()

cleanup = regex.compile(
        r"(?(DEFINE)"
            + r"(?<op>[!=|&<>+\-/*%^~{}[\]():;,?])"
            + r"(?<tgt>(?:\s|/\*(?:.|\n)*?\*/|//.*?$)+)"
        + r") (?:\".*?\"|'.*?')(*SKIP)(*F)"
        + r"| \A(?&tgt) | (?&tgt)\Z | (?<sp>(?<=:)(?&tgt)(?=:))"
        + r"| (?&tgt)(?=(?&op)) | (?<=(?&op))(?&tgt) | (?<sp>(?&tgt))",
        regex.M|regex.X
    )

findDirectives = regex.compile(
        r"<(?<tag>\w+?)(?<selfend>/)?> (?(selfend)|(?<contents>.*?) </(?P=tag)>)",
        regex.X|regex.S
    )

dirRemove = "remove".casefold()
    

def findSource(mergeList, mergePath, extension):
    mergeListData = None
    with open(mergeList, "r") as f:
        mergeListData = json.load(f)

    for k in mergeListData:
        mergeListData[k] = [
            os.path.join(mergePath, file + extension)
            for file in mergeListData[k]
            if os.path.exists(os.path.join(mergePath, file + extension))
        ]

    return mergeListData

def _replaceWhitespace(match):
    return " " if match.group("sp") else ""

def executeDirectives(text):
    for match in findDirectives.finditer(text):
        if match.group("tag").casefold() == dirRemove:
            text = text[:match.start()] + text[match.end():]

    return text

def processFile(file):
    out = None

    with open(file, "r") as f:
        out = f.read()

    out = executeDirectives(out)
    out = cleanup.sub(_replaceWhitespace, out)
    return out

def makeMerged(files, headerFile):
    out = None
    
    with open(headerFile, "r") as f:
        out = f.read()
    
    for file in files:
        out += processFile(file)

    return out

#files = findSource(mergeList, mergePath)
#print(makeMerged(files["vs_library"], headerFile))
