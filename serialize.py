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
Contains serialization capability
'''

import binascii
import pickle
from io import BytesIO
import router
import utils
import spacing


def serialize(bit, boards, sp, config, description):
    '''
    Serializes the arguments. Returns the serialized string, which can
    later be used to reconstruct the arguments using unserialize()
    '''
    out = BytesIO()

    p = pickle.Pickler(out)
    # Save code version
    p.dump(utils.VERSION)
    # Save the units
    units = bit.units
    p.dump(units.metric)
    p.dump(units.num_increments)
    # Save the bit
    p.dump(bit.width)
    p.dump(bit.depth)
    p.dump(bit.angle)
    # Save the board info
    nb = len(boards)
    p.dump(nb)
    for b in boards:
        p.dump(b.width)
        p.dump(b.height)
        p.dump(b.wood)
        p.dump(b.active)
        p.dump(b.dheight)
    # Save the spacing
    sp_type = sp.__class__.__name__[0:4]
    if config.debug:
        print('serialize', sp_type)
    p.dump(sp_type)
    if sp_type == 'Edit':
        p.dump(sp.cuts)
    else:
        p.dump(sp.params)
    p.dump(description)
    s = out.getvalue()
    out.close()
    if config.debug:
        print('size of pickle', len(s))
    ret = binascii.b2a_qp(s).decode('utf-8')
    return ret


def unserialize(s, config, newformat=False, transl=None):
    '''
    Unserializes the string s, and returns the tuple (bit, boards, spacing)
    '''
    # new format uue encoding support
    if newformat:
        s = binascii.a2b_qp(s)
    else:
        s = s.encode()

    inp = BytesIO(s)

    u = pickle.Unpickler(inp)

    description = None
    version = u.load()
    if config.debug:
        print('unserialized version:', version)
    # form the units
    metric = u.load()
    num_increments = u.load()
    units = utils.Units(config.english_separator, metric, num_increments, transl)
    # form the bit
    width = u.load()
    depth = u.load()
    angle = u.load()
    bit = router.Router_Bit(units, width, depth, angle)
    # form the boards
    nb = u.load()
    boards = []
    for _ in range(nb):
        boards.append(router.Board(bit, 10))  # dummy width argument, for now
    for b in boards:
        b.width = u.load()
        b.height = u.load()
        b.wood = u.load()
        b.active = u.load()
        b.dheight = u.load()
    # form the spacing
    sp_type = u.load()
    if sp_type == 'Edit':
        if config.debug:
            print('unserialized edit spacing')
        cuts = u.load()
        sp = spacing.Edit_Spaced(bit, boards, config)
        sp.set_cuts(cuts)
    else:
        if sp_type == 'Equa':
            sp = spacing.Equally_Spaced(bit, boards, config)
        else:
            sp = spacing.Variable_Spaced(bit, boards, config)
        sp.params = u.load()
        if newformat:   #compatibility please for all new params
            description = u.load()
        else:
            sp.upgrade()

        if config.debug:
            print('unserialized ', sp_type, str(sp.params))

        sp.set_cuts()
    return (bit, boards, sp, sp_type, description)
