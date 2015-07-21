# -*- coding: utf-8 -*-
"""
/***************************************************************************
        begin                : 2015-07-21
        git sha              : $Format:%H$
        copyright            : (C) 2015 by David Erill
        email                : daviderill79@gmail.com
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

from PyQt4 import QtGui
from ui.select_trees_dialog import Ui_selectTreesDockWidget

# cannot apply dynamic loading because cannot promote widget 
# belongin to othe modules
# import os
# from PyQt4 import uic
# FORM_CLASS, _ = uic.loadUiType(os.path.join(
#     os.path.dirname(__file__), 'ui', 'search_plus_dialog_base.ui'))
# class selectTreesDockWidget(QtGui.QDockWidget, FORM_CLASS):

class SelectTreesDockWidget(QtGui.QDockWidget, Ui_selectTreesDockWidget):
    
    def __init__(self, parent=None):
        """Constructor."""
        super(SelectTreesDockWidget, self).__init__(parent)
        
        # Set up the user interface from Designer.
        self.setupUi(self)