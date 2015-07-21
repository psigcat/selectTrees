# -*- coding: utf-8 -*-
"""
/***************************************************************************
        begin                : 2015-07-21
        git sha              : $Format:%H$
        copyright            : (C) 2015 by David Erill
        email                : daviderilll79@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'David Erill'
__date__ = 'July 2015'
__copyright__ = '(C) 2015, David Erill'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import os
import sys

curpath = os.path.dirname(os.path.realpath(__file__))

# Adding so that our UI files can find resources_rc.py which is up one level.
sys.path.append(os.path.join(curpath, '..'))
