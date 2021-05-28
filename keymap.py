#!/usr/bin/env python3

"""
This script will convert a properly formatted .yaml file specifying a keymap
into a LaTeX file, which is then run to generate a .pdf of the keymap.

The keymap is presented as a .yaml file that consists of a `keyboard` item
that specifies both `rows` and `columns` (as integers), and a series of layer
names. Each layer must have the following items, with corresponding number of
elements:
  `keys`:      list of rows, where each row is a list of keys
  `rowcombos`: list of rows, where each row is a list of combos between keys
               on that row. There should be 2 fewer items in a row than the
               number of columns.
  `colcombos`: list of rows, where each row is a list of combos between keys
               on vertically adjacent columns. There should be 1 fewer row in
               this list than the number of rows on the keyboard overall.
Each of these keys and combos is LaTeX string to be printed in the keyboard
layout. Locations where a key should not be printed are identified as `None`.

Optionally, each layer *may* include the following lists of [row_number,
column_number], both 0-based:
  `lines`:   keys to receive a horizontal line dividing them in half
  `shading`: keys to be shaded

Hint: Certain strings in YAML files must be escaped or quoted. Using single
quotes is best where possible, and a single quote character can be
represented within single quotes by doubling it: `''''` in a field will
produce `'`. (If using double quotes, `\` must itself be escaped, and so will
need to be doubled up; hence `\\\\\\` will produce `\\\`.)

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

\\usepackage{fancyhdr}
\\pagestyle{fancy}
\\lhead{NAME}
\\rhead{\\today}
\\cfoot{}

\\begin{document}

\\thispagestyle{fancy}
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


def createLayer(layer, rows, columns, keyLayout):
    # Generate LaTeX code for key layout of given layer
    # Start with comment identifying new layer; add layer header
    latex = "\n\n" + "%" * 78 + "\n"
    latex += "% " + int((68-len(layer))/2 + .5) * " "
    latex += layer.upper() + " LAYER " + int((68-len(layer))/2) * " "
    latex += "%\n" + "%" * 78 + "\n\n"
    latex += LAYERHEADER
    latex += createTitle(layer, rows)

    try:
        shadeList = keyLayout[layer]["shading"]
    except KeyError:
        shadeList = []
    try:
        lineList = keyLayout[layer]["lines"]
    except KeyError:
        lineList = []

    for row in range(rows):
        thisRow = keyLayout[layer]["keys"][row]
        latex += "\n% Row #" + str(rows - row - 1) + "\n"
        for column in range(columns):
            if str(thisRow[column]) != "None":  # Don't print a key if `None`
                if column < columns / 2:  # Calculate horiz spacing for columns
                    horiz = -SEPARATION - KEYSPACEHORIZ * (columns / 2 - 1
                                                           - column)
                else:
                    horiz = SEPARATION + KEYSPACEHORIZ * (column - columns / 2)
                latex += "\\node [" + addShading(rows - row - 1, column,
                                                 shadeList) \
                    + "rectStyle] " \
                    + "(key-" + str(column) + "-" + str(rows - row - 1) \
                    + ") at (" + str(horiz) + " in, " \
                    + str(KEYSPACEVERT * (rows - row - 1)) + " in) " \
                    + "{" + str(thisRow[column]) + "};\n"
                # Add a horizontal line if needed
                latex += addLine(rows - row - 1, column, lineList)

    return latex


def createRowCombos(layer, rows, columns, keyLayout):
    # Generate LaTeX code for combos between keys in a given row
    latex = ""
    for row in range(rows):
        latex += "\n% Row Combos: Row #" + str(rows - row - 1) + "\n"
        thisRow = keyLayout[layer]["rowcombos"][row]
        for column in range(columns - 2):
            if str(thisRow[column]) != "":
                if column < columns / 2 - 1:  # Calculate horiz spacing for columns
                    horiz = -SEPARATION - KEYSPACEHORIZ * (columns / 2 - column
                                                           - 1.5)
                else:
                    horiz = SEPARATION + KEYSPACEHORIZ * (column - columns / 2
                                                          + 1.5)
                latex += "\\node [hcomboStyle] at (" \
                    + str(horiz) + " in, " \
                    + str(KEYSPACEVERT * (rows - row - 1)) + " in) " \
                    + "{\\vspace{-1.25\\baselineskip}" + str(thisRow[column]) \
                    + "};\n"
    return latex


def createColCombos(layer, rows, columns, keyLayout):
    # Generate LaTeX code for combos between keys in a given column
    latex = ""
    for row in range(rows - 1):
        latex += "\n% Column Combos: Rows #" + str(rows - row - 1) + "-" \
            + str(rows - row - 2) + "\n"
        thisRow = keyLayout[layer]["colcombos"][row]
        for column in range(columns):
            if str(thisRow[column]) != "":
                if column < 5:  # Calculate horizontal spacing for columns
                    horiz = -SEPARATION - KEYSPACEHORIZ * (4-column)
                else:
                    horiz = SEPARATION + KEYSPACEHORIZ * (column-5)
                latex += "\\node [vcomboStyle] at " \
                    + "(" + str(horiz) + " in, " \
                    + str(KEYSPACEVERT * (rows-row-1.5)) + " in) " \
                    + "{" + str(thisRow[column]) + "};\n"
    return latex


def createTitle(layer, rows):
    # Put layer name as large label in middle-top of keyboard layout
    latex = "\n% Layer Name\n"
    latex += "\\node at (0," + str((rows - 1) * KEYSPACEVERT) + " in) " \
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
    except KeyError:
        print("ERROR: Must have a top-level YAML entry for 'keyboard',")
        print("identifying both 'rows' and 'columns' fields")
        exit(1)
    try:
        name = keyLayout['keyboard']['name']
        del keyLayout['keyboard']
    except KeyError:
        name = 'TESTING'

    document = HEADER.replace("NAME", name)

    for layer in keyLayout.keys():
        # Add in code for each row of layer's layout (including combos)
        document += createLayer(layer, rows, columns, keyLayout)
        document += createRowCombos(layer, rows, columns, keyLayout)
        document += createColCombos(layer, rows, columns, keyLayout)
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

    print(path.join(tempdir, root + ".tex"))

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
