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
import pymesh
import numpy as np
from numpy.linalg import norm
from scipy import spatial
from ldrawpy import *
from cqkit import *

scriptdir = os.path.dirname(os.path.realpath(__file__))

srcdir = os.path.normpath(scriptdir + os.path.sep + "../STEP/Metal")
outdir = os.path.normpath(scriptdir + os.path.sep + "../ldraw")
subdir = os.path.normpath(scriptdir + os.path.sep + "../ldraw/s")

MIN_RES = 0.05
CIRCLE_RES = 24
CURVE_RES = 10

# files = [ "R56" ]
files = [ "R56", "R64", "R72", "R88", "R104", "R120", "S8", "S16", "S32" ]

def log_mesh(mesh, msg=None, edges=None):
    s = msg if msg is not None else ""
    es = "edges=%-5d " % (len(edges)) if edges is not None else ""
    print("Mesh:  triangles=%-5d vertices=%-5d %s%s" % (len(mesh.vertices), len(mesh.faces), es, s))

def fix_mesh(mesh):
    mesh, __ = pymesh.remove_degenerated_triangles(mesh, 100)
    log_mesh(mesh, "Remove degenerate faces")
    mesh, __ = pymesh.collapse_short_edges(mesh, MIN_RES, preserve_feature=True)
    log_mesh(mesh, "Collapse short edges")
    mesh = pymesh.resolve_self_intersection(mesh)
    mesh, __ = pymesh.remove_duplicated_faces(mesh)
    log_mesh(mesh, "Remove self intersections")
    mesh = pymesh.compute_outer_hull(mesh)
    mesh, __ = pymesh.remove_duplicated_faces(mesh)
    log_mesh(mesh, "New hull, remove duplicates")
    mesh, __ = pymesh.remove_obtuse_triangles(mesh, 179.5, 5)
    log_mesh(mesh, "Remote obtuse faces")
    mesh, __ = pymesh.remove_isolated_vertices(mesh)
    log_mesh(mesh, "Remove isolated vertices")
    return mesh

def ldr_header(fn, prefix=""):
    head, tail = os.path.split(fn)
    h = LDRHeader()
    h.author = "Fx Bricks"
    h.title = prefix + " " + tail
    h.file = tail
    h.name = str(tail).lower()
    s = []
    s.append(str(h))
    s.append("0 !LDRAW_ORG Unofficial_Part\n")
    s.append("0 !LICENSE Redistributable under CCAL version 2.0 : see CAreadme.txt\n")
    s.append("0 BFC CERTIFY CCW\n")
    return "".join(s)

def mesh_object(fnstl, fnstep, fnout): 
    print("Importing %s..." % (fnstl))
    mesh = pymesh.load_mesh(fnstl)
    log_mesh(mesh, "Imported mesh")
    mesh = fix_mesh(mesh)
    mv = []
    for v in mesh.vertices:
        mv.append(Vector(tuple(v)))
    obj = import_step_file(fnstep)
    edges = obj.edges().vals()
    log_mesh(mesh, msg="Imported STEP", edges=edges)

    print("Discretizing edges...")
    edges = discretize_all_edges(edges, curve_res=CURVE_RES, circle_res=CIRCLE_RES, as_pts=True)
    log_mesh(mesh, edges=edges)

    vertices = np.array(mesh.vertices)
    epts = []
    for e in edges:
        e0 = list(e[0])
        e1 = list(e[1])
        p0 = tuple(vertices[spatial.distance.cdist([e0], vertices).argmin()])
        p1 = tuple(vertices[spatial.distance.cdist([e1], vertices).argmin()])
        p0 = p0 if abs(Vector(p0) - Vector(tuple(e0))) < 0.2 else e0
        p1 = p1 if abs(Vector(p1) - Vector(tuple(e1))) < 0.2 else e1
        epts.append((p0, p1))

    log_mesh(mesh, edges=epts)
    ldr_obj = mesh_to_ldr(
        mesh.faces, mv, LDR_DEF_COLOUR, epts, LDR_OPT_COLOUR
    )
    hs = ldr_header(fnout, prefix="Fx_Track")
    f = open(fnout, "w")
    f.write(hs)
    f.write(ldr_obj)
    f.write("0 NOFILE\n")
    f.close()

def get_filenames(path, obj, ext, prefix="Test"):
    return {
        "step": os.path.normpath(path + os.sep + "Simple-%s-NoDraft-Plain-NoRad.%s" % (obj, ext)),
        "track": os.path.normpath(path + os.sep + "Fx%s.%s" % (obj, ext)),
        "inner": os.path.normpath(path + os.sep + "%s-%s-InnerRail.%s" % (prefix, obj, ext)),
        "outer": os.path.normpath(path + os.sep + "%s-%s-OuterRail.%s" % (prefix, obj, ext)),
    }    


for f in files:
    fnstl = get_filenames(srcdir, f, "stl")
    fnstep = get_filenames(srcdir, f, "step")
    fnout = get_filenames(subdir, f, "dat", prefix="Metal")
    mesh_object(fnstl["track"], fnstep["step"], fnout["track"])
    mesh_object(fnstl["inner"], fnstep["inner"], fnout["inner"])
    mesh_object(fnstl["outer"], fnstep["outer"], fnout["outer"])

    fn = os.path.normpath(outdir + os.sep + "%s_Metal.dat" % (f))
    hs = ldr_header(fn, prefix="Fx_Track")
    fp = open(fn, "w")
    fp.write(hs)
    p = LDRPart()
    p.attrib.colour = 72
    head, tail = os.path.split(fnout["track"])
    p.name = "s/%s" % (tail)
    fp.write(str(p))
    p = LDRPart()
    p.attrib.colour = 383
    head, tail = os.path.split(fnout["inner"])
    p.name = "s/%s" % (tail)
    fp.write(str(p))
    p = LDRPart()
    p.attrib.colour = 383
    head, tail = os.path.split(fnout["outer"])
    p.name = "s/%s" % (tail)
    fp.write(str(p))
    fp.write("0 NOFILE\n")
    fp.close()

# mesh_object(fnstl, fnstep, fnout): 