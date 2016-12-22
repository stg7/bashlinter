#!/usr/bin/env python3
#   Copyright 2016-today
#
#   bash code convention checker,
#   based on google style guide (https://google.github.io/styleguide/shell.xml)
#
#   Author: Steve Göring
#
#
#   This file is part of bashlinter.
#
#   bashlinter is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   bashlinter is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with bashlinter.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import re
import argparse


def colorred(m):
    return "\033[91m" + m + "\033[0m"


def colorblue(m):
    return "\033[94m" + m + "\033[0m"


def colorgreen(m):
    return "\033[92m" + m + "\033[0m"


def colorcyan(m):
    return "\033[96m" + m + "\033[0m"


def logInfo(msg):
    print(colorgreen("[INFO ] ") + str(msg))


def logError(msg):
    print(colorred("[ERROR] ") + str(msg))


def logDebug(msg):
    print(colorblue("[DEBUG] ") + str(msg))


def logWarn(msg):
    print(colorcyan("[WARN ] ") + str(msg))


def checkFile(filename):
    logInfo("handle file: " + filename)
    f = open(filename, "r")
    linenumber = 1

    # better rules map
    project = False
    copyright = False
    usageDef = False
    mainDef = False
    mainCall = False
    tabsUsed = False
    multi4SpacesIdent = True
    commentStartWithSpace = True
    author = False
    correctIf = True
    openIf = False
    correctCase = True
    openCase = False
    correctFor = True
    openForLoop = False
    correctWhile = True
    openWhileLoop = False
    correctBashSubCall = True
    correctFunctionDef = True

    errorcount = 0
    lineNumberMap = {}
    for l in f:
        l = l.replace("\n", "")
        # each file starts with #!/bin/bash
        if linenumber == 1:
            if l != "#!/bin/bash" and l != "#!/usr/bin/env bash":
                logError("file have to start with #!/bin/bash or #!/usr/bin/env bash, fix it!")
                return
            linenumber += 1
            continue

        if "#" in l and "project" in l.lower():
            project = True

        if "#" in l and "copyright" in l.lower():
            copyright = True
        if "#" in l and "author" in l.lower():
            author = True
        if "usage()" in l:
            usageDef = True
        if "main()" in l:
            mainDef = True
        if 'main "$@"' in l:
            mainCall = True
        if "\t" in l:
            tabsUsed = True
            errorcount += 1
            lineNumberMap["tabs"] = lineNumberMap.get("tabs", []) + [linenumber]

        if len(l) != 0 and l[0] == " ":
            countleadingspaces = 0
            for i in range(len(l)):
                if l[i] == " ":
                    countleadingspaces += 1
                else:
                    break
            if countleadingspaces % 4 != 0:
                multi4SpacesIdent = False
                errorcount += 1
                lineNumberMap["4spaces"] = lineNumberMap.get("4spaces", []) + [linenumber]

        if "#" in l and l[-1] != "#" and l[l.find("#") + 1] != " " and "$#" not in l and \
                (re.match(".*\".*#.*\".*", l) is None) and \
                (re.match(".*'.*#.*'.*", l) is None):
            commentStartWithSpace = False
            errorcount += 1
            lineNumberMap["commentStartWithSpace"] = lineNumberMap.get("commentStartWithSpace", []) + [linenumber]

        # if statement
        if "if" in l and ("#" not in l or l.find("#") > l.find("if")) and \
                ("$if" not in l) and \
                (re.match(".*if[a-z,A-z,0-9]*.*", l) is None) and \
                (re.match("if \[.*\]; then", l.strip()) is None) and \
                (re.match(".*$(.*if.*).*", l) is None) and \
                (re.match(".*\".*if.*\".*", l) is None) and \
                (re.match(".*'.*if.*'.*", l) is None):
            correctIf = False
            errorcount += 1
            lineNumberMap["if"] = lineNumberMap.get("if", []) + [linenumber]
            openIf = True
        if openIf and "else" in l and l.strip() != "else":
            correctIf = False
            errorcount += 1
            lineNumberMap["if"] = lineNumberMap.get("if", []) + [linenumber]
        if openIf and "fi" in l and re.match(".*\".*fi.*", l) is None:
            openIf = False
            if len(l.strip()) != len(l):
                correctIf = False
                errorcount += 1
                lineNumberMap["if"] = lineNumberMap.get("if", []) + [linenumber]

        # case statement
        if "case" in l and ("#" not in l or l.find("#") > l.find("case")) and re.match("case .* in", l.strip()) is None:
            correctCase = False
            errorcount += 1
            lineNumberMap["case"] = lineNumberMap.get("case", []) + [linenumber]
            openCase = True
        if openCase and "esac" in l:
            openCase = False
            if l.strip() != "esac":
                correctCase = False
                lineNumberMap["case"] = lineNumberMap.get("case", []) + [linenumber]
                errorcount += 1

        # for loop
        if "for" in l and re.match(".*\".*for.*", l) is None and ("#" not in l or l.find("#") > l.find("for")) and re.match("for .* in .*; do", l.strip()) is None and \
                (re.match(".*for[a-z,A-z,0-9]*.*", l) is None):
            correctFor = False
            lineNumberMap["for"] = lineNumberMap.get("for", []) + [linenumber]
            openForLoop = True
            errorcount += 1

        if openForLoop and "done" in l:
            openForLoop = False
            if l.strip() != "done":
                correctFor = False
                errorcount += 1
                lineNumberMap["for"] = lineNumberMap.get("for", []) + [linenumber]

        # while loop
        if "while" in l and ("#" not in l or l.find("#") > l.find("while")) and\
                re.match("while \[ .* \]; do", l.strip()) is None and\
                re.match(".*while .*; do", l.strip()) is None:
            correctWhile = False
            errorcount += 1
            lineNumberMap["while"] = lineNumberMap.get("while", []) + [linenumber]
            openWhileLoop = True
        if openWhileLoop and "done" in l:
            openWhileLoop = False
            if l.strip() != "done":
                correctWhile = False
                lineNumberMap["while"] = lineNumberMap.get("while", []) + [linenumber]
                errorcount += 1
        # bash sub call
        if "`" in l or "´" in l:
            correctBashSubCall = False
            lineNumberMap["bashsubcall"] = lineNumberMap.get("bashsubcall", []) + [linenumber]
            errorcount += 1

        # function definitions:
        if re.match("function .*()", l.strip()) is not None:
            correctFunctionDef = False
            lineNumberMap["funcdef"] = lineNumberMap.get("funcdef", []) + [linenumber]
            errorcount += 1

        linenumber += 1

    if not project:
        logError("file needs a project description")
        errorcount += 1
    if not copyright:
        logError("file needs a copyright description")
        errorcount += 1
    if not usageDef:
        logWarn("file should have a usage function")
    if not mainDef:
        logWarn("file should have a main method")
        errorcount += 1
    if mainDef and not mainCall:
        logError("file needs a correct main function call: e.g. main \"$@\"")
        errorcount += 1
    if not author:
        logError("file needs an author")
        errorcount += 1

    if tabsUsed:
        logError("identation with tabs detected, uses multiple of 4 spaces! " + str(lineNumberMap["tabs"]))
    if not multi4SpacesIdent:
        logError("identation have to be multiple of 4 spaces: lines: " + str(lineNumberMap["4spaces"]))
    if not commentStartWithSpace:
        logError("comment need space after hashtag, not: '#Comment', better: '# Comment', lines:" + str(lineNumberMap["commentStartWithSpace"]))
    if not correctIf:
        logError("if statement not correct, should be 'if [ .. ]; then'" + str(lineNumberMap["if"]))
    if not correctCase:
        logError("case statement not correct, should be 'case ... in'" + str(lineNumberMap["case"]))
    if not correctFor:
        logError("for statement not correct, should be 'for .. in ..; do'" + str(lineNumberMap["for"]))
    if not correctWhile:
        logError("while statement not correct, should be while [ .. ]; do" + str(lineNumberMap["while"]))
    if not correctBashSubCall:
        logError("dont use `prog`, better use $(prog)" + str(lineNumberMap["bashsubcall"]))
    if not correctFunctionDef:
        logError("invalid function definition, should be 'functionname() {'" + str(lineNumberMap["funcdef"]))

    if errorcount != 0:
        logWarn(str(errorcount) + " errors detected in `{}`".format(filename))
        sys.exit(-1)
    else:
        logInfo("everything is ok")
    f.close()

    return


def main(params):
    parser = argparse.ArgumentParser(description='Bash Linter', epilog="stg7 2017", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('inputfile', nargs="+", type=str, help="input bash file")

    argsdict = vars(parser.parse_args())
    for bashfile in argsdict["inputfile"]:
        checkFile(bashfile)

if __name__ == "__main__":
    main(sys.argv[1:])
