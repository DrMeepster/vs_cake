import json, os, sys, re

mergeList = "merge_list.json"
mergePath = "vs_library"
headerFile = "header.txt"

cleanup = re.compile(
    r"(?: //.*?$ | /\*.*?\*/ | \s )+ | (?P<keep> \".*?\" | '.*?' )",
    re.M | re.X | re.S
)

despace = re.compile(
      "  \A\ "
    + "| \ \Z"
    + "| (?<=[!=|&<>+\-/*%^~{}[\]():;,?]) \  (?!:)"
    + "| (?<!:) \  (?=[!=|&<>+-/*%^~{}[\]():;,?])"
    + "| \ (?=\")"
    + "| (?<=\")\ "
    + "| \ (?=')"
    + "| (?<=')\ "
    + "| (?P<keep> \".*?\" | '.*?' )",
    re.M | re.X | re.S
)

def findSource(mergeList, mergePath, extension=".nut"):
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

def processFile(file):
    out = None

    with open(file, "r") as f:
        out = f.read()

        def replaceMatch(match):
            keep = match.group("keep")
            if keep:
                return keep
            else:
                return " "
        
        #remove comments and new lines
        out = cleanup.sub(replaceMatch, out)

        #remove extra spaces created
        out = despace.sub(r"\g<keep>", out)
    return out

def makeMerged(files, headerFile):
    out = None
    
    with open(headerFile, "r") as f:
        out = f.read()
    
    for file in files:
        out += processFile(file)

    return out

files = findSource(mergeList, mergePath)
print(makeMerged(files["vs_library"], headerFile))
