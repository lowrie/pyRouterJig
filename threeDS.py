###########################################################################
#
# Copyright 2015-2018 Robert B. Lowrie (http://github.com/lowrie)
#
# This file is part of pyRouterJig.
#
# pyRouterJig is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pyRouterJig is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# pyRouterJig; see the file LICENSE. If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################

'''
Contains functionality for writing Autodesk 3DS files.
'''
from __future__ import division
from __future__ import print_function
from future.utils import lrange
from io import StringIO

import struct, copy
import router


class BinaryIO(StringIO):
    def writepack(self, fmt, *values):
        '''Writes data with little-endian, packed with struct'''
        self.write(struct.pack('<' + fmt, *values))


class Object_Geometry(object):
    '''Geometry information for a single 3DS object'''
    def __init__(self, name, vertices, triangles):
        self.name = name
        self.vertices = vertices
        self.triangles = triangles

    def num_vertices(self):
        return len(self.vertices)

    def num_triangles(self):
        return len(self.triangles)


def write_3ds(filename, objects):
    '''
    Writes objects to filename in 3DS format, where objects is a list of Object_Geometrys.
    '''

    key3ds = {

        #------ Primary chunk

        'MAIN3DS': 0x4D4D,

        #------ Main Chunks

        'EDIT3DS': 0x3D3D,
        'KEYF3DS': 0xB000,

        #------ sub defines of EDIT3DS

        'EDIT_MATERIAL': 0xAFFF,
        'EDIT_CONFIG1': 0x0100,
        'EDIT_CONFIG2': 0x3E3D,
        'EDIT_VIEW_P1': 0x7012,
        'EDIT_VIEW_P2': 0x7011,
        'EDIT_VIEW_P3': 0x7020,
        'EDIT_VIEW1': 0x7001,
        'EDIT_BACKGR': 0x1200,
        'EDIT_AMBIENT': 0x2100,
        'EDIT_OBJECT': 0x4000,

        #------ sub defines of EDIT_OBJECT
        'OBJ_TRIMESH': 0x4100,
        'OBJ_LIGHT': 0x4600,
        'OBJ_CAMERA': 0x4700,

        'OBJ_UNKNWN01': 0x4010,
        'OBJ_UNKNWN02': 0x4012,  #>---- Could be shadow

        #------ sub defines of OBJ_CAMERA
        'CAM_UNKNWN01': 0x4710,
        'CAM_UNKNWN02': 0x4720,

        #------ sub defines of OBJ_LIGHT
        'LIT_OFF': 0x4620,
        'LIT_SPOT': 0x4610,
        'LIT_UNKNWN01': 0x465A,

        #------ sub defines of OBJ_TRIMESH
        'TRI_VERTEXL': 0x4110,
        'TRI_FACEL2': 0x4111,
        'TRI_FACEL1': 0x4120,
        'TRI_SMOOTH': 0x4150,
        'TRI_LOCAL': 0x4160,
        'TRI_VISIBLE': 0x4165,

        #------ sub defs of KEYF3DS

        'KEYF_FRAMES': 0xB008,
        'KEYF_OBJDES': 0xB002,

        #------  these define the different color chunk types
        'COL_RGB': 0x0010,
        'COL_TRU': 0x0011,
        'COL_UNK': 0x0013,

        #------ defines for viewport chunks

        'TOP': 0x0001,
        'BOTTOM': 0x0002,
        'LEFT': 0x0003,
        'RIGHT': 0x0004,
        'FRONT': 0x0005,
        'BACK': 0x0006,
        'USER': 0x0007,
        'CAMERA': 0x0008,  # 0xFFFF is the actual code read from file
        'LIGHT': 0x0009,
        'DISABLED': 0x0010,
        'BOGUS': 0x0011
    }

    n = len(objects)
    tri_vertexl_size = [8] * n
    tri_facel1_size = [8] * n
    obj_trimesh_size = [6] * n
    edit_object_size = [6] * n
    name = [''] * n
    edit3ds_size = 6
    main3ds_size = 6
    # determine the size of each chunk
    for i in lrange(n):
        tri_vertexl_size[i] += 4 * 3 * objects[i].num_vertices()
        tri_facel1_size[i] += 2 * 4 * objects[i].num_triangles()
        obj_trimesh_size[i] += tri_vertexl_size[i] + tri_facel1_size[i]
        name[i] = objects[i].name + '\0'
        edit_object_size[i] += obj_trimesh_size[i] + len(name[i])
        edit3ds_size += edit_object_size[i]
    main3ds_size += edit3ds_size
    # pack up the chunks into a buffer
    bio = BinaryIO()
    bio.writepack('HI', key3ds['MAIN3DS'], main3ds_size)
    bio.writepack('HI', key3ds['EDIT3DS'], edit3ds_size)
    for i in lrange(n):
        bio.writepack('HI', key3ds['EDIT_OBJECT'], edit_object_size[i])
        bio.write(name[i])
        bio.writepack('HI', key3ds['OBJ_TRIMESH'], obj_trimesh_size[i])
        bio.writepack('HI', key3ds['TRI_VERTEXL'], tri_vertexl_size[i])
        bio.writepack('H', objects[i].num_vertices())
        for v in objects[i].vertices:
            bio.writepack('fff', v[0], v[1], v[2])
        bio.writepack('HI', key3ds['TRI_FACEL1'], tri_facel1_size[i])
        bio.writepack('H', objects[i].num_triangles())
        for t in objects[i].triangles:
            bio.writepack('HHHH', t[0], t[1], t[2], 0x0006)
    s = bio.getvalue()
    # print len(s), main3ds_size
    # Write the buffer to the file
    fd = open(filename, 'wb')
    fd.write(s)
    fd.close()


def extrude(v2d, tri2d, order, z1, z2, units):
    if units.metric:
        scale = 1.0
    else:
        scale = 1.0 / units.increments_per_inch
    nv2d = len(v2d)
    ntri2d = len(tri2d)
    v3d = [[0, 0, 0]] * (nv2d * 2)
    i = 0
    i2 = nv2d
    for v in v2d:
        v1 = [v[0] * scale, v[1] * scale, z1 * scale]
        v2 = [v[0] * scale, v[1] * scale, z2 * scale]
        v3d[i] = [v1[order[0]], v1[order[1]], v1[order[2]]]
        v3d[i2] = [v2[order[0]], v2[order[1]], v2[order[2]]]
        i += 1
        i2 += 1
    tri3d = [[0, 0, 0]] * (2 * ntri2d)
    i = 0
    i2 = ntri2d
    for t in tri2d:
        tri3d[i] = [t[0], t[1], t[2]]
        tri3d[i2] = [t[0] + nv2d, t[1] + nv2d, t[2] + nv2d]
        i += 1
        i2 += 1
    for i in lrange(nv2d):
        ip = i + 1
        ie = i + nv2d
        iep = ie + 1
        if ip == nv2d:
            ip = 0
            iep = nv2d
        tri3d.append([i, ip, iep])
        tri3d.append([i, iep, ie])
    return (v3d, tri3d)


def joint_to_3ds(filename, boards, bit, spacing):
    bc = copy.deepcopy(boards)
    router.cut_boards(bc, bit, spacing)
    for b in bc:
        b.set_origin(0, 0)
    objects = []
    bc[1].set_origin(0, -(bc[1].yT() - bit.depth))
    (v2d, tri2d) = bc[0].triangulate(bit)
    (v3dtop, tri3dtop) = extrude(v2d, tri2d, (0, 1, 2), 0, bit.depth, bit.units)
    objects.append(Object_Geometry('top', v3dtop, tri3dtop))
    (v2d, tri2d) = bc[1].triangulate(bit)
    (v3dbot, tri3dbot) = extrude(v2d, tri2d, (0, 2, 1), 0, bit.depth, bit.units)
    objects.append(Object_Geometry('top', v3dbot, tri3dbot))
#
#    v3d = []
#    for v in v2d:
#        v3d.append([v[0], v[1], 0])
#    objects = [Object_Geometry('top', v3d, tri2d)]
#
    write_3ds(filename, objects)
    

if __name__ == '__main__':
    v1 = [[0, 0, 0],
          [1, 0, 0],
          [0, 1, 0],
          [1, 1, 0],
          [0.25, 1.00, 0],
          [0.75, 1.00, 0],
          [0.25, 1.50, 0],
          [0.75, 1.50, 0]]

    t1 = [[0, 1, 3],
          [0, 3, 2],
          [4, 5, 7],
          [4, 7, 6]]

    t1a = [[0, 4, 2],
           [0, 1, 4],
           [1, 5, 4],
           [1, 3, 5],
           [4, 5, 7],
           [4, 7, 6]]

    v2 = [[0, 0, 1],
          [1, 0, 1],
          [0, 1, 1],
          [1, 1, 1]]

    t2 = [[0, 1, 3],
          [0, 3, 2]]

    objects = [Object_Geometry('dog', v1, t1a), Object_Geometry('catss', v2, t2)]

    write_3ds('dog.3ds', objects)

