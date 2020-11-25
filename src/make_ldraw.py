#! /usr/bin/env python3
#
# Copyright (C) 2020  Fx Bricks
# This file is part of the legocad python module.
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# LDraw Model conversion script

import os

from ldrawpy import *
from cqkit import *

scriptdir = os.path.dirname(os.path.realpath(__file__))

srcdir = os.path.normpath(scriptdir + os.path.sep + "../STEP")
outdir = os.path.normpath(scriptdir + os.path.sep + "../ldraw")
subdir = os.path.normpath(scriptdir + os.path.sep + "../ldraw/s")

files = {
    "PFxBrick": {
        "subfiles": [
            ("s/PFxBaseV2.dat", 72),
            ("s/PFxLidV2.dat", 71),
            ("s/PFxPCBV2.dat", 0),
            ("s/USBShellV2.dat", 494),
            ("s/USBPlasticV2.dat", 0),
            ("s/USBPinsV2.dat", 82),
            ("s/PFPins.dat", 82),
            ("s/LightPipe.dat", 34),
            ("s/Screws.dat", 494),
        ],
        "outfile": "PFxBrickV2.dat",
    },
    "PFxBaseV2": {"srcfile": "PFxBaseV2.step", "outfile": "s/PFxBaseV2.dat"},
    "PFxLidV2": {"srcfile": "PFxLidV2.step", "outfile": "s/PFxLidV2.dat"},
    "PFxPCBV2": {"srcfile": "PFxPCBV2.step", "outfile": "s/PFxPCBV2.dat"},
    "PFPins": {"srcfile": "PFPins.step", "outfile": "s/PFPins.dat",},
    "LightPipe": {"srcfile": "LightPipe.step", "outfile": "s/LightPipe.dat",},
    "Screws": {"srcfile": "Screws.step", "outfile": "s/Screws.dat",},
    "USBShellV2": {"srcfile": "USBShellV2.step", "outfile": "s/USBShellV2.dat",},
    "USBPinsV2": {"srcfile": "USBPinsV2.step", "outfile": "s/USBPinsV2.dat",},
    "USBPlasticV2": {"srcfile": "USBPlasticV2.step", "outfile": "s/USBPlasticV2.dat",},
    "XLSpeakerV2": { "subfiles": [
        ("s/XLSpeakerCase.dat", 71),
        ("s/XLSpeakerCone.dat", 0),
        ],
        "outfile": "XLSpeakerV2.dat",
    },
    # "XLSpeakerCase": {"srcfile": "XLSpeakerCase.step", "outfile": "s/XLSpeakerCase.dat"},
    # "XLSpeakerCone": {"srcfile": "XLSpeakerCone.step", "outfile": "s/XLSpeakerCone.dat"},
}


def ldr_header(fn):
    outfile = os.path.normpath(outdir + os.sep + fn)
    head, tail = os.path.split(outfile)
    h = LDRHeader()
    h.author = "Fx Bricks"
    h.title = tail
    h.file = tail
    h.name = str(tail).lower()
    return str(h)


for k, v in files.items():
    outfile = os.path.normpath(outdir + os.sep + v["outfile"])
    hs = ldr_header(outfile)

    if "srcfile" in v:
        fn = os.path.normpath(srcdir + os.sep + v["srcfile"])
        print("Importing %s..." % (fn))
        obj = import_step_file(fn)
        solid = obj.vals()
        edges = obj.edges().vals()
        triangles, vertices = triangle_mesh_solid(solid, lin_tol=5e-2, ang_tol=0.5)
        edges = discretize_all_edges(edges, curve_res=12, circle_res=24, as_pts=True)
        print("Vertices: %d" % (len(vertices)))
        print("triangles: %d" % (len(triangles)))
        print("Edges: %d" % (len(edges)))
        ldr_obj = mesh_to_ldr(
            triangles, vertices, LDR_DEF_COLOUR, edges, LDR_OPT_COLOUR
        )
        f = open(outfile, "w")
        f.write(hs)
        f.write(ldr_obj)
        f.write("0 NOFILE\n")
        f.close()

    elif "subfiles" in v:
        f = open(outfile, "w")
        f.write(hs)
        for sub in v["subfiles"]:
            p = LDRPart()
            p.attrib.colour = sub[1]
            p.name = sub[0]
            f.write(str(p))
        f.write("0 NOFILE\n")
        f.close()

