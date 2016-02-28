###########################################################################
#
# Copyright 2015-2016 Robert B. Lowrie (http://github.com/lowrie)
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
Contains functionality for displaying a table of router pass locations.
'''
from __future__ import division
from __future__ import print_function
from future.utils import lrange

import utils
import router

def print_table(filename, boards, title):
    '''
    Prints a table of router pass locations, referenced to the right size of the board.
    '''
    # Load up the cuts and labels to be printed
    all_cuts = [boards[0].bottom_cuts]
    label_cuts = ['A']
    labels = ['B', 'C', 'D', 'E', 'F']
    i = 0
    if boards[3].active:
        all_cuts.append(boards[3].top_cuts)
        label_cuts.append(labels[i])
        all_cuts.append(boards[3].bottom_cuts)
        label_cuts.append(labels[i + 1])
        i += 2
    if boards[2].active:
        all_cuts.append(boards[2].top_cuts)
        label_cuts.append(labels[i])
        all_cuts.append(boards[2].bottom_cuts)
        label_cuts.append(labels[i + 1])
        i += 2
    all_cuts.append(boards[1].top_cuts)
    label_cuts.append(labels[i])
    # TODO: add cauls
    # Format for each pass, location pair
    form = ' %4s %9s '
    # Print the header
    line = ''
    for k in label_cuts:
        s = 'Pass'
        line += form % (s, 'Location')
    lenh = len(line)
    divider = '-' * lenh + '\n'
    line = divider + line + '\n' + divider
    fd = open(filename, 'w')
    fd.write(title + '\n')
    fd.write(line)
    # Initialize for the print loop
    ncol = len(all_cuts)
    width = boards[0].width
    units = boards[0].units
    pass_index = [0] * ncol
    cut_index = [0] * ncol
    for icol in lrange(ncol):
        cut_index[icol] = len(all_cuts[icol]) - 1
    total_passes = [0] * ncol
    # Print until all of the edges are out of passes.  We go through the cuts,
    # and each pass in the cut, in reverse order (from right to left).
    printing = True
    while printing:
        line = ''
        printing = False
        # Loop through the edges
        for icol in lrange(ncol):
            label = '**'
            dim = '**'
            # check if there are any more passes for this edge
            icut = cut_index[icol]
            if icut >= 0:
                # Still have a pass, so load it
                c = all_cuts[icol][icut]
                np = len(c.passes)
                pi = pass_index[icol]
                total_passes[icol] += 1
                label = '%d%s' % (total_passes[icol], label_cuts[icol])
                dim = units.increments_to_string(width - c.passes[np - pi - 1])
                pass_index[icol] += 1
                printing = True
                # if we are done with this cut, go on to the next cut
                if pass_index[icol] == np:
                    cut_index[icol] -= 1
                    pass_index[icol] = 0
            line += form % (label, dim)
        if printing:
            fd.write(line + '\n')
    fd.close()
