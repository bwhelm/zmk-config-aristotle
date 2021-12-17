---
title: Notes on ZMK Installation/Use
author:
date:
# GENERAL FORMATTING
fontsize: 11pt
fancyhdr: plain
geometry: ipad
numbersections: true
# DRAFT SPECS: use `draft`, `print`, or `hide`
draft: true
draftfooter: true
---

# Installation

1. Install zephyr

2. Put the following in `.zshrc`:

        export ZEPHYR_TOOLCHAIN_VARIANT=cross-compile
        export CROSS_COMPILE=/usr/local/bin/arm-none-eabi-

# Building

Once installation is set up, should be able to build firmware with:

    west build -p -b nice_nano -- -DSHIELD=aristotle-33

# Transforms

Here's the matrix of the keyboard:

|        | **C0** | **C1** | **C2** | **C3** | **C4** | **C5** | **C6** | **C7** | **C8** |
|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| **R0** | K00    | K01    | K02    | K03    | K04    | K05    | K06    | K07    | --     |
| **R1** | K09    | K10    | K11    | K12    | K13    | K14    | K15    | K16    | K17    |
| **R2** | K19    | K20    | K21    | K22    | K23    | K24    | K25    | K26    | K27    |
| **R3** | K08    | K28    | K18    | K29    | K30    | K31    | --     | --     | --     |

These keys correspond to a physical layout that looks like this:

| **C0** | **C1** | **C2** | **C3** | **C4** |  | **C5** | **C6** | **C7** | **C8** | **C9** |
|--------|--------|--------|--------|--------|--|--------|--------|--------|--------|--------|
|        | K00    | K01    | K02    | K03    |  | K04    | K05    | K06    | K07    |        |
| K08    | K09    | K10    | K11    | K12    |  | K13    | K14    | K15    | K16    | K17    |
| K18    | K19    | K20    | K21    | K22    |  | K23    | K24    | K25    | K26    | K27    |
|        |        |        | K28    | K29    |  | K30    | K31    |        |        |        |

That means, the corresponding transform will look like this (where first digit is the row number and second digit is the column number from the matrix of the keys as physically laid out):

| **C0** | **C1** | **C2** | **C3** | **C4** |  | **C5** | **C6** | **C7** | **C8** | **C9** |
|--------|--------|--------|--------|--------|--|--------|--------|--------|--------|--------|
|        | 00     | 01     | 02     | 03     |  | 04     | 05     | 06     | 07     |        |
| 30     | 10     | 11     | 12     | 13     |  | 14     | 15     | 16     | 17     | 18     |
| 32     | 20     | 21     | 22     | 23     |  | 24     | 25     | 26     | 27     | 28     |
|        |        |        | 31     | 33     |  | 34     | 35     |        |        |        |

This is what I should put into the RC(x, y) settings in the .overlay file.

# Things to Implement

1. MOUSE layer. Create a new one, using left left thumb, and putting all controls on right hand.

# Questions

1. Is there a way to set the board from power up to run `&out OUT_BLE`? <https://zmkfirmware.dev/docs/behaviors/outputs/>
    - One thing I need to check is whether when the MCU is plugged into a charger it thinks it's a real USB device and sends keystrokes to it rather than over Bluetooth.
