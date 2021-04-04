#!/usr/bin/env python3

from os import path
from ruamel.yaml import YAML
from ruamel.yaml.composer import ComposerError
from shutil import copy
import subprocess
from sys import argv
from tempfile import gettempdir


# VARIABLES. DISTANCES ARE IN INCHES
rotAngle = 0
separation = 1.0
keySizeHoriz = .55
keySizeVert = .55
keySepHoriz = .2
keySepVert = .2
keySpaceHoriz = keySizeHoriz + keySepHoriz
keySpaceVert = keySizeVert + keySepVert
yoffset = [0, 0, 0, 0, 0]
# rounding = keySepVert
# margin = .13

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


def createRow(row, rowNum):  # Generate LaTeX code for standard rows
    latex = "\n% Row #" + str(rowNum) + "\n"
    for col in [0, 1, 2, 3, 4]:
        # rotate = "rotate around={" + str(-rotAngle) + ":(" \
        #     + str(-separation + keySizeHoriz / 2) + "in, " \
        #     + str(-keySizeVert / 2) + ")}] "
        # latex += "\\node [rectStyle, " + rotate \
        latex += "\\node [rectStyle] " \
            + "(left-" + str(col) + "-" + str(rowNum) + ") at " \
            + "(" + str(-separation - keySpaceHoriz * (4 - col)) + " in, " \
            + str(yoffset[4 - col] + keySpaceVert * rowNum) + " in) " \
            + "{" + row[col] + "};\n"

    for col in [5, 6, 7, 8, 9]:
        # rotate = "rotate around={" + str(rotAngle) + ":(" \
        #     + str(separation - keySizeHoriz / 2) + "in, " \
        #     + str(-keySizeVert / 2) + "in)}] "
        # latex += "\\node [rectStyle, " + rotate \
        latex += "\\node [rectStyle] " \
            + "(right-" + str(col) + "-" + str(rowNum) + ") at " \
            + "(" + str(separation + keySpaceHoriz * (col - 5)) + " in, " \
            + str(yoffset[col - 5] + keySpaceVert * rowNum) + " in) " \
            + "{" + row[col] + "};\n"

    return latex


def createThumb(row, rowNum):  # Generate LaTeX code for thumb row
    shading = "fill=black!7,"
    latex = "\n% Thumb Keys\n"
    latex += "\\node ["
    if rowNum == 1:
        latex += shading
    latex += "rectStyle] (left-t-1) at " \
        + "(" + str(-separation + keySpaceHoriz / 2) + " in, " \
        + str(-keySpaceVert) + " in) " \
        + "{" + row[0] + "};\n"
    latex += "\\node ["
    if rowNum == 2:
        latex += shading
    latex += "rectStyle] (right-t-1) at "\
        + "(" + str(separation - keySpaceHoriz / 2) + " in, " \
        + str(-keySpaceVert) + " in) " \
        + "{" + row[1] + "};\n"
    latex += "\\node ["
    if rowNum == 3:
        latex += shading
    latex += "rectStyle] (right-t-0) at "\
        + "(" + str(separation + keySpaceHoriz / 2) + " in, " \
        + str(-keySpaceVert) + " in) " \
        + "{" + row[2] + "};\n"
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
        + str(rowNum + 1) + "\n"
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
    latex += "\\node at (0,3.8) {\\huge\\textsc{" + layer + "}};\n"
    return latex


def readYaml(file):  # Read in YAML file
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    yaml = YAML(typ='safe')
    try:
        k = yaml.load(text)
    except ComposerError as e:
        print("ERROR: Cannot parse " + path.abspath(file) + "!")
        print(e)
        exit(1)
    return k


def main(file):
    # Generate LaTeX document
    k = readYaml(file)
    document = header
    counter = -1
    for layer in k.keys():
        counter += 1
        document += "\n\n" + "%" * 78 + "\n"
        document += "% " + int((68-len(layer))/2 + .5) * " "
        document += layer.upper() + " LAYER " + int((68-len(layer))/2) * " "
        document += "%\n" + "%" * 78 + "\n\n"
        document += layerHeader

        document += createRow(k[layer]["top"], 2)
        document += createRow(k[layer]["mid"], 1)
        document += createRow(k[layer]["bot"], 0)
        document += createThumb(k[layer]["thumb"], counter)
        document += rowCombo(k[layer]["tcomb"], 2)
        document += rowCombo(k[layer]["mcomb"], 1)
        document += rowCombo(k[layer]["bcomb"], 0)
        document += colCombo(k[layer]["tmcomb"], 2)
        document += colCombo(k[layer]["mbcomb"], 1)

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
