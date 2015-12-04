###########################################################################
#
# Copyright 2015 Robert B. Lowrie (http://github.com/lowrie)
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
from __future__ import print_function
from future.utils import lrange

import pickle, StringIO
from options import OPTIONS
import router
import utils
import spacing

spacing_idmap = {'Equa':0, 'Vari':1, 'Edit':2}

def serialize(bit, board, sp):
    '''
    Serializes the arguments. Returns the serialized string, which can
    later be used to reconstruct the arguments using unserialize_joint()
    '''
    out = StringIO.StringIO()
    p = pickle.Pickler(out)
    # Save code version
    p.dump(utils.VERSION)
    # Save the units
    units = bit.units
    p.dump(units.metric)
    if not units.metric:
        p.dump(units.increments_per_inch)
    # Save the bit
    p.dump(bit.width)
    p.dump(bit.depth)
    p.dump(bit.angle)
    # Save the board
    p.dump(board.width)
    # Save the spacing
    sp_type = sp.description[0:4]
    if OPTIONS['debug']:
        print('serialize', sp_type)
    p.dump(sp_type)
    if sp_type == 'Edit':
        p.dump(sp.cuts)
    else:
        p.dump(sp.params)
    s = out.getvalue()
    out.close()
    if OPTIONS['debug']:
        print('size of pickle', len(s))
    return s

def unserialize(s):
    '''
    Unserializes the string s, and returns the tuple (bit, board, spacing)
    '''
    inp = StringIO.StringIO(s)
    u = pickle.Unpickler(inp)
    version = u.load()
    if OPTIONS['debug']:
        print('unserialized version', version)
    # form the units
    metric = u.load()
    if metric:
        if OPTIONS['debug']:
            print('unserialized metric')
        units = utils.Units(metric=True)
    else:
        ipi = u.load()
        if OPTIONS['debug']:
            print('unserialized increments_per_inch', ipi)
        units = utils.Units(ipi)
    # form the bit
    width = u.load()
    depth = u.load()
    angle = u.load()
    if OPTIONS['debug']:
        print('unserialized bit w,d,a', width, depth, angle)
    bit = router.Router_Bit(units, width, depth, angle)
    # form the board
    width = u.load()
    board = router.Board(bit, width)
    if OPTIONS['debug']:
        print('unserialized board width', width)
    # form the spacing
    sp_type = u.load()
    if sp_type == 'Edit':
        if OPTIONS['debug']:
            print('unserialized edit spacing')
        cuts = u.load()
        sp = spacing.Edit_Spaced(bit, board)
        sp.set_cuts(cuts)
    else:
        if sp_type == 'Equa':
            sp = spacing.Equally_Spaced(bit, board)
        else:
            sp = spacing.Variable_Spaced(bit, board)
        sp.params = u.load()
        if OPTIONS['debug']:
            print('unserialized ', sp_type, `sp.params`)
        sp.set_cuts()
    return (bit, board, sp, sp_type)
