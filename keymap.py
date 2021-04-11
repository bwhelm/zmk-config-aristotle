#!/usr/bin/env python3

"""

This script will convert a properly formatted YAML file specifying a keymap
into a LaTeX file, which is then run to generate a .pdf of the keymap.

The keymap is presented as a YAML file that consists of a series of layer
names. Each layer must have the following items, with corresponding number of
elements:

- `top`: top row (10 keys)
- `mid`dle: middle row (10 keys)
- `bot`tom: bottom row (10 keys)
- `thumb`: thumb row (10 keys)
- `tcomb`: combos between horizontally adjacent top-row keys (8 items)
- `mcomb`: combos between horizontally adjacent middle-row keys (8 items)
- `bcomb`: combos between horizontally adjacent bottom-row keys (8 items)
- `tmcomb`: combos between vertically adjacent keys between top and middle rows
            (10 items)
- `mbcomb`: combos between vertically adjacent keys between middle and bottom
            rows (10 items)

Each of these items is a list of LaTeX strings to be printed in the keyboard
layout. Locations where a key should not be printed are identified as `None`.

Optionally, each layer *may* include the following lists of [row_number,
column_number], both 0-based:

- `lines`: keys to receive a horizontal line dividing them in half
- `shading`: keys to be shaded

Hint: Certain strings in YAML files must be escaped or quoted. Using single
quotes is best where possible, and a single quote character can be
represented within single quotes by doubling it: `''''` in a field will
produce `'`.

"""

from os import path
from ruamel.yaml import YAML
from ruamel.yaml.composer import ComposerError
from shutil import copy
import subprocess
from sys import argv
from tempfile import gettempdir


# VARIABLES. DISTANCES ARE IN INCHES
SEPARATION = 1.0
KEYSIZEHORIZ = .55
KEYSIZEVERT = .55
KEYSEPHORIZ = .2
KEYSEPVERT = .2
KEYSPACEHORIZ = KEYSIZEHORIZ + KEYSEPHORIZ
KEYSPACEVERT = KEYSIZEVERT + KEYSEPVERT
SHADING = "fill=black!7,"

# Identify row numbers for each row label
itemRowNums = dict()
itemRowNums["top"] = 3
itemRowNums["mid"] = 2
itemRowNums["bot"] = 1
itemRowNums["thumb"] = 0

HEADER = '''\\documentclass[]{article}
\\usepackage[oldstyle,sups]{fbb}% to use free Bembo font (old style numbers)
\\usepackage[margin=.75in]{geometry}
\\pagestyle{empty}
\\usepackage[T1]{fontenc}
\\usepackage[utf8]{inputenc}
\\usepackage{textcomp} % provide euro and other symbols
\\usepackage{fontawesome}
\\usepackage{menukeys}
\\usepackage{tikz}
\\usetikzlibrary{shapes}

% Manually define visible space (which otherwise doesn't appear in fbb font)
\\newsavebox{\\textvisiblespacebox}
\\savebox{\\textvisiblespacebox}{M}
\\newcommand\\vtextvisiblespace[1][\\wd\\textvisiblespacebox]{%
  \\makebox[#1]{\\kern.1em\\rule{.4pt}{.3ex}%
  \\hrulefill%
  \\rule{.4pt}{.3ex}\\kern.1em}%
}

\\begin{document}
'''

LAYERHEADER = '''\\begin{centering}

\\resizebox{6.33in}{!}{%  Make `\\textwidth` for portrait; `9in` for landscape.

\\begin{tikzpicture}[
    rectStyle/.style={inner sep=0pt,minimum size=''' + str(KEYSIZEVERT) + ''' in,draw,font=\\Large,align=center},
    vcomboStyle/.style={minimum width=''' + str(KEYSIZEHORIZ) + ''', align=center, font=\\Large},
    hcomboStyle/.style={minimum width=''' + str(KEYSEPHORIZ) + ''', align=center, font=\\Large},
    ]
'''

LAYERFOOTER = '''
\\end{tikzpicture}

} % resize box

\\vspace{.4in}

\\end{centering}
'''

FOOTER = "\n\\end{document}"


def addShading(row, col, shadeList):
    if [row, col] in shadeList:
        return SHADING
    else:
        return ""


def addLine(row, col, lineList):
    if [row, col] in lineList:
        key = "key-" + str(col) + "-" + str(row)
        return "\\draw [color=gray] (" + key + ".west) -- (" \
            + key + ".east);\n"
    else:
        return ""


def createRow(keyLayout, layer, item):
    # Generate LaTeX code for standard rows
    row = keyLayout[layer][item]
    try:
        shadeList = keyLayout[layer]["shading"]
    except KeyError:
        shadeList = []
    try:
        lineList = keyLayout[layer]["lines"]
    except KeyError:
        lineList = []
    rowNum = itemRowNums[item]
    latex = "\n% Row #" + str(rowNum) + "\n"
    for col in range(10):
        if str(row[col]) != "None":  # Don't print a key if `None`
            if col < 5:  # Calculate horizontal spacing for columns
                horiz = -SEPARATION - KEYSPACEHORIZ * (4 - col)
            else:
                horiz = SEPARATION + KEYSPACEHORIZ * (col - 5)
            latex += "\\node [" + addShading(rowNum, col, shadeList) \
                + "rectStyle] " \
                + "(key-" + str(col) + "-" + str(rowNum) + ") at " \
                + "(" + str(horiz) + " in, " \
                + str(KEYSPACEVERT * rowNum) + " in) " \
                + "{" + str(row[col]) + "};\n"
            # Add a horizontal line if needed
            latex += addLine(rowNum, col, lineList)
    return latex


def rowCombo(row, rowNum):
    # Generate LaTeX code for combos between keys on a given row
    latex = "\n% Combos: Row #" + str(rowNum) + "\n"
    for col in range(8):
        if str(row[col]) != "":
            if col < 5:  # Calculate horizontal spacing for columns
                horiz = -SEPARATION - KEYSPACEHORIZ * (4-col - .5)
            else:
                horiz = SEPARATION + KEYSPACEHORIZ * (col-4 + .5)
            latex += "\\node [hcomboStyle] at (" \
                + str(horiz) + " in, " \
                + str(KEYSPACEVERT * rowNum) + " in) " \
                + "{\\vspace{-1.25\\baselineskip}" + str(row[col]) + "};\n"
    return latex


def colCombo(row, rowNum):
    # Generate LaTeX code for combos between keys in a given column
    latex = "\n% Column Combos: Rows #" + str(rowNum) + "--" \
        + str(rowNum+1) + "\n"
    for col in range(10):
        if str(row[col]) != "":
            if col < 5:  # Calculate horizontal spacing for columns
                horiz = -SEPARATION - KEYSPACEHORIZ * (4-col)
            else:
                horiz = SEPARATION + KEYSPACEHORIZ * (col-5)
            latex += "\\node [vcomboStyle] at " \
                + "(" + str(horiz) + " in, " \
                + str(KEYSPACEVERT * (rowNum-.5)) + " in) " \
                + "{" + str(row[col]) + "};\n"
    return latex


def createTitle(layer):
    # Put layer name as large label in middle-top of keyboard layout
    latex = "\n% Layer Name\n"
    latex += "\\node at (0," + str(3 * KEYSPACEVERT) + " in) " \
        "{\\huge\\textsc{" + layer + "}};\n"
    return latex


def readYaml(file):  # Read in YAML file
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    yaml = YAML(typ='safe')
    try:
        keyLayout = yaml.load(text)
    except ComposerError as e:
        print("ERROR: Cannot parse " + path.abspath(file) + "!")
        print(e)
        exit(1)
    return keyLayout


def main(file):
    # Generate LaTeX document
    keyLayout = readYaml(file)
    try:
        rows = keyLayout['keyboard']['rows']
        columns = keyLayout['keyboard']['columns']
        del keyLayout['keyboard']
    except KeyError:
        print("ERROR: Must have a top-level YAML entry for 'keyboard',")
        print("identifying both 'rows' and 'columns' fields")
        exit(1)
    document = HEADER

    for layer in keyLayout.keys():
        # Put comment in document identifying new layer; add layer header
        document += "\n\n" + "%" * 78 + "\n"
        document += "% " + int((68-len(layer))/2 + .5) * " "
        document += layer.upper() + " LAYER " + int((68-len(layer))/2) * " "
        document += "%\n" + "%" * 78 + "\n\n"
        document += LAYERHEADER

        # Add in code for each row of layer's layout (including combos)
        document += createRow(keyLayout, layer, "top")
        document += createRow(keyLayout, layer, "mid")
        document += createRow(keyLayout, layer, "bot")
        document += createRow(keyLayout, layer, "thumb")
        document += rowCombo(keyLayout[layer]["tcomb"], 3)
        document += rowCombo(keyLayout[layer]["mcomb"], 2)
        document += rowCombo(keyLayout[layer]["bcomb"], 1)
        document += colCombo(keyLayout[layer]["tmcomb"], 3)
        document += colCombo(keyLayout[layer]["mbcomb"], 2)

        document += createTitle(layer)
        document += LAYERFOOTER

    document += FOOTER

    # Write document to file in temporary directory
    tempdir = gettempdir()
    name = path.basename(file)
    root, ext = path.splitext(name)
    outputFile = path.join(tempdir, root + ".tex")
    with open(outputFile, "w") as f:
        f.write(document)

    # Process with LaTeX
    command = "latexmk -cd -pdf " + outputFile
    try:
        subprocess.call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(e)
        subprocess.call("open " + path.join(tempdir, root + ".log"),
                        shell=True)
        exit(1)

    # Copy result and open in Skim
    copy(path.join(tempdir, root + ".pdf"), "./" + root + ".pdf")
    subprocess.call("open -ga /Applications/Skim.app ./" + root + ".pdf",
                    shell=True)


if __name__ == "__main__":
    if len(argv) != 2:
        print("Must provide a single .yaml file to process!")
        exit(1)
    file = argv[1]
    if not path.isfile(file):
        print(path.abspath(file) + " is not a file!")
        exit(1)

    main(file)
