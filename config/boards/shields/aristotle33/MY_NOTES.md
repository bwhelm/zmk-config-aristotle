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

2. Put the following in .zshrc:

        export ZEPHYR_TOOLCHAIN_VARIANT=cross-compile
        export CROSS_COMPILE=/usr/local/bin/arm-none-eabi-

# Building

Once installation is set up, should be able to build firmware with:

    west build -p -b nice_nano -- -DSHIELD=aristotle-33

# Transforms

Here's the matrix of the keyboard:

|        | **C0** | **C1** | **C2** | **C3** | **C4** | **C5** | **C6** | **C7** | **C8** |
|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| **R0** | K01    | K02    | K03    | K34    | K09    | K08    | K07    | K06    | K05    |
| **R1** | K00    | K11    | K12    | K04    | K19    | K18    | K17    | K16    | K15    |
| **R2** | K10    | K21    | K13    | K14    | K29    | K28    | K27    | K26    | K25    |
| **R3** | K20    | K22    | K23    | K24    | K39    | K38    | --     | --     | --     |

These keys correspond to a physical layout that looks like this:

| **C0** | **C1** | **C2** | **C3** | **C4** |  | **C5** | **C6** | **C7** | **C8** | **C9** |
|--------|--------|--------|--------|--------|--|--------|--------|--------|--------|--------|
| K00    | K01    | K02    | K03    | K04    |  | K09    | K08    | K07    | K06    | K05    |
| K10    | K11    | K12    | K13    | K14    |  | K19    | K18    | K17    | K16    | K15    |
| K20    | K21    | K22    | K23    | K24    |  | K29    | K28    | K27    | K26    | K25    |
|        |        |        |        | K34    |  | K39    | K38    |        |        |        |

That means, the corresponding transform will look like this (where first digit is the row number and second digit is the column number from the matrix of the keys as physically laid out):

| **C0** | **C1** | **C2** | **C3** | **C4** |  | **C5** | **C6** | **C7** | **C8** | **C9** |
|--------|--------|--------|--------|--------|--|--------|--------|--------|--------|--------|
| 10     | 00     | 01     | 02     | 13     |  | 04     | 05     | 06     | 07     | 08     |
| 20     | 11     | 12     | 22     | 23     |  | 14     | 15     | 16     | 17     | 18     |
| 30     | 21     | 31     | 32     | 33     |  | 24     | 25     | 26     | 27     | 28     |
|        |        |        |        | 03     |  | 34     | 35     |        |        |        |

This is what I should put into the RC(x, y) settings in the .overlay file.

# Things to Implement

1. DEFAULT layer:
    1. Need to update &mt keys ... setting tapping term and other things.
        - I think I can define different types of behaviors, each with its own tapping term. So while I can't get per-key tapping terms, I can get something pretty close.
    2. Need to fix &lt for MAC. Perhaps this is done, but I need to test...

2. NUMBER layer

3. FUNCTION layer
    - I think this is all working properly.

4. MACRO layer.
    - I can't get mouse keys just yet, so that's not working.
    - Otherwise, I think things should work.

5. GENERALLY:
    1. Need to test COMBOS.
    2. Look into changing the BT power level by including this or something similar in .conf file:

        CONFIG_BT_CTLR_TX_PWR_MINUS_20=y

# Questions

1. Is there a way to set the board from power up to run `&out OUT_BLE`? <https://zmkfirmware.dev/docs/behaviors/outputs/>
    - One thing I need to check is whether when the MCU is plugged into a charger it thinks it's a real USB device and sends keystrokes to it rather than over Bluetooth.

2. Is there a way to print out (as if one were typing) the current battery level? (In QMK, there are various hooks that allow a fair bit of customizability in what one can do with particular keystrokes. I'm not seeing that in the ZMK docs.)
