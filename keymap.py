#!/usr/bin/env python3

"""
This script will convert a properly formatted .yaml file specifying a keymap
into a LaTeX file, which is then run to generate a .pdf of the keymap.

The keymap is presented as a .yaml file with three main entries: `layout`,
`shading`, and `lines`. `shading` and `lines` are lists of keys that are to
be shaded or have horizontal lines added. `layout` specifies the keyboard
layout.

The layout consists of a set of layer names, under which are specifications
(as lists of LaTeX strings) of what characters are printed in the `top` row
(10 items), the `mid`dle row (10 items), the `bot`tom row (10 items), and the
`thumb` row (3 items). In addition, the layout must specify horizontal
combinations for the top (`tcomb`), middle `(`mcomb`), and bottom (`bcomb`)
rows. The assumption here is that combinations will only involve adjacent
keys, and so there will be 8 locations for such combinations for each row.
Finally, the layout must specify vertical combinations for adjacent keys
between the top and middle rows (`tmcomb`) and the middle and bottom rows
(`mbcomb`); each of these is a list of 10 items.
"""

from os import path
from ruamel.yaml import YAML
from ruamel.yaml.composer import ComposerError
from shutil import copy
import subprocess
from sys import argv
from tempfile import gettempdir


# VARIABLES. DISTANCES ARE IN INCHES
separation = 1.0
keySizeHoriz = .55
keySizeVert = .55
keySepHoriz = .2
keySepVert = .2
keySpaceHoriz = keySizeHoriz + keySepHoriz
keySpaceVert = keySizeVert + keySepVert
yoffset = [0, 0, 0, 0, 0]
shading = "fill=black!7,"

header = '''\\documentclass[]{article}
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

layerHeader = '''\\begin{centering}

\\resizebox{6.33in}{!}{%  Make `\\textwidth` for portrait; `9in` for landscape.

\\begin{tikzpicture}[
    rectStyle/.style={inner sep=0pt,minimum size=''' + str(keySizeVert) + ''' in,draw,font=\\Large,align=center},
    vcomboStyle/.style={minimum width=''' + str(keySizeHoriz) + ''', align=center, font=\\Large},
    hcomboStyle/.style={minimum width=''' + str(keySepHoriz) + ''', align=center, font=\\Large},
    ]
'''

layerFooter = '''
\\end{tikzpicture}

} % resize box

\\vspace{.4in}

\\end{centering}
'''

footer = "\n\\end{document}"


def addShading(layer, row, col, shadeList):
    if [layer, row, col] in shadeList:
        return shading
    else:
        return ""


def addLine(layer, row, col, lineList):
    if [layer, row, col] in lineList:
        key = "key-" + str(col) + "-" + str(row)
        return "\\draw [color=gray] (" + key + ".west) -- (" \
            + key + ".east);\n"
    else:
        return ""


def createRow(row, rowNum, layer, keyboard):
    # Generate LaTeX code for standard rows
    latex = "\n% Row #" + str(rowNum) + "\n"
    for col in [0, 1, 2, 3, 4]:
        latex += "\\node [" + addShading(layer, rowNum, col,
                                         keyboard["shading"]) \
            + "rectStyle] " \
            + "(key-" + str(col) + "-" + str(rowNum) + ") at " \
            + "(" + str(-separation - keySpaceHoriz * (4 - col)) + " in, " \
            + str(yoffset[4 - col] + keySpaceVert * rowNum) + " in) " \
            + "{" + row[col] + "};\n"
        latex += addLine(layer, rowNum, col, keyboard["lines"])

    for col in [5, 6, 7, 8, 9]:
        latex += "\\node [" + addShading(layer, rowNum, col,
                                         keyboard["shading"]) \
            + "rectStyle] " \
            + "(key-" + str(col) + "-" + str(rowNum) + ") at " \
            + "(" + str(separation + keySpaceHoriz * (col - 5)) + " in, " \
            + str(yoffset[col - 5] + keySpaceVert * rowNum) + " in) " \
            + "{" + row[col] + "};\n"
        # Add a horizontal line if needed
        latex += addLine(layer, rowNum, col, keyboard["lines"])

    return latex


def createThumb(row, layer, keyboard):  # Generate LaTeX code for thumb row
    latex = "\n% Thumb Keys\n"
    latex += "\\node [" + addShading(layer, 0, 0, keyboard["shading"]) \
        + "rectStyle] (key-4-0) at " \
        + "(" + str(-separation + keySpaceHoriz / 2) + " in, " \
        + "0 in) " \
        + "{" + row[0] + "};\n"
    latex += addLine(layer, 0, 4, keyboard["lines"])
    latex += "\\node [" + addShading(layer, 0, 1, keyboard["shading"]) \
        + "rectStyle] (key-5-0) at "\
        + "(" + str(separation - keySpaceHoriz / 2) + " in, " \
        + "0 in) " \
        + "{" + row[1] + "};\n"
    latex += addLine(layer, 0, 5, keyboard["lines"])
    latex += "\\node [" + addShading(layer, 0, 2, keyboard["shading"]) \
        + "rectStyle] (key-6-0) at "\
        + "(" + str(separation + keySpaceHoriz / 2) + " in, " \
        + "0 in) " \
        + "{" + row[2] + "};\n"
    latex += addLine(layer, 0, 6, keyboard["lines"])
    return latex


def rowCombo(row, rowNum):
    # Generate LaTeX code for combos between keys on a given row
    latex = "\n% Combos: Row #" + str(rowNum) + "\n"
    for col in [0, 1, 2, 3]:
        if row[col] != "":
            latex += "\\node [hcomboStyle] at (" \
                + str(-separation - keySpaceHoriz * (4-col - .5)) + " in, " \
                + str(yoffset[4-col] + keySpaceVert * rowNum) + " in) " \
                + "{\\vspace{-1.25\\baselineskip}" + row[col] + "};\n"
    for col in [4, 5, 6, 7]:
        if row[col] != "":
            latex += "\\node [hcomboStyle] at (" \
                + str(separation + keySpaceHoriz * (col-4 + .5)) + " in, " \
                + str(yoffset[col-4] + keySpaceVert * rowNum) + " in) " \
                + "{" + row[col] + "};\n"
    return latex


def colCombo(row, rowNum):
    # Generate LaTeX code for combos between keys in a given column
    latex = "\n% Column Combos: Rows #" + str(rowNum) + "--" \
        + str(rowNum+1) + "\n"
    for col in [0, 1, 2, 3, 4]:
        if row[col] != "":
            latex += "\\node [vcomboStyle] at " \
                + "(" + str(-separation - keySpaceHoriz * (4-col)) + " in, " \
                + str(yoffset[4-col] + keySpaceVert * (rowNum-.5)) + " in) " \
                + "{" + row[col] + "};\n"
    for col in [5, 6, 7, 8, 9]:
        if row[col] != "":
            latex += "\\node [vcomboStyle] at (" \
                + str(separation + keySpaceHoriz * (col-5)) + " in, " \
                + str(yoffset[col-5] + keySpaceVert * (rowNum-.5)) + " in) " \
                + "{" + row[col] + "};\n"
    return latex


def createTitle(layer):
    latex = "\n% Layer Name\n"
    latex += "\\node at (0," + str(2 * keySpaceVert) + " in) " \
        "{\\huge\\textsc{" + layer + "}};\n"
    return latex


def readYaml(file):  # Read in YAML file
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    yaml = YAML(typ='safe')
    try:
        keyboard = yaml.load(text)
    except ComposerError as e:
        print("ERROR: Cannot parse " + path.abspath(file) + "!")
        print(e)
        exit(1)
    return keyboard


def main(file):
    # Generate LaTeX document
    keyboard = readYaml(file)
    keyLayout = keyboard["layout"]
    document = header
    counter = -1
    for layer in keyLayout.keys():
        counter += 1
        document += "\n\n" + "%" * 78 + "\n"
        document += "% " + int((68-len(layer))/2 + .5) * " "
        document += layer.upper() + " LAYER " + int((68-len(layer))/2) * " "
        document += "%\n" + "%" * 78 + "\n\n"
        document += layerHeader

        document += createRow(keyLayout[layer]["top"], 3, layer, keyboard)
        document += createRow(keyLayout[layer]["mid"], 2, layer, keyboard)
        document += createRow(keyLayout[layer]["bot"], 1, layer, keyboard)
        document += createThumb(keyLayout[layer]["thumb"], layer, keyboard)
        document += rowCombo(keyLayout[layer]["tcomb"], 3)
        document += rowCombo(keyLayout[layer]["mcomb"], 2)
        document += rowCombo(keyLayout[layer]["bcomb"], 1)
        document += colCombo(keyLayout[layer]["tmcomb"], 3)
        document += colCombo(keyLayout[layer]["mbcomb"], 2)

        document += createTitle(layer)
        document += layerFooter

    document += footer

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
    subprocess.call("open -ga /Applications/Skim.app " +
                    path.join(tempdir, root + ".pdf"),
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
