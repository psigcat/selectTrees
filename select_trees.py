# -*- coding: utf-8 -*-
"""
/***************************************************************************
        begin                : 2015-07_21
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
# 2To3 python compatibility
#from __future__ import unicode_literals, division, print_function

from qgis.utils import active_plugins
from qgis.gui import (QgsMessageBar, QgsTextAnnotationItem)
from qgis.core import (QgsCredentials, QgsDataSourceURI, QgsGeometry, QgsPoint, QgsLogger, QgsExpression, QgsFeatureRequest)
from PyQt4.QtCore import (QObject, QSettings, QTranslator, qVersion, QCoreApplication, Qt, pyqtSignal, QPyNullVariant)
from PyQt4.QtGui import (QAction, QIcon, QDockWidget, QTextDocument, QIntValidator, QLabel, QComboBox)

# PostGIS import
import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)# Initialize Qt resources from file resources.py
import resources_rc

# Import the code for the dialog
from select_trees_dockwidget import SelectTreesDockWidget
import os.path

import sys  
#reload(sys)  
sys.setdefaultencoding('utf8')


class SelectTrees(QObject):
    """QGIS Plugin Implementation."""

    #connectionEstablished = pyqtSignal()

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        super(SelectTrees, self).__init__()
        
        # Save reference to the QGIS interface
        self.iface = iface
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        self.pluginName = os.path.basename(self.plugin_dir)
        
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        self.locale_path = os.path.join(self.plugin_dir, 'i18n', 'SelectTrees_{}.qm'.format(locale))
        if os.path.exists(self.locale_path):
            self.translator = QTranslator()
            self.translator.load(self.locale_path)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        
        # load local settings of the plugin
        settingFile = os.path.join(self.plugin_dir, 'config', 'SelectTrees.config')
        self.settings = QSettings(settingFile, QSettings.IniFormat)
        #self.settings.setIniCodec(sys.stdout.encoding)
        
        # load plugin settings
        self.loadPluginSettings()
        
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SelectTrees')
        self.annotations = []
        self.toolbar = self.iface.addToolBar(u'SelectTrees')
        self.toolbar.setObjectName(u'SelectTrees')
        self.layer = None        
        
        # establish connection when all is completely running 
        #self.iface.initializationCompleted.connect(self.populateGui)
              
   
    def loadPluginSettings(self):
        ''' Load plugin settings
        '''       
        # Get main credentials
        self.TOTAL = 6
        self.SECTION = "main/"
        
        # Get layer name
        self.layer_name = self.settings.value(self.SECTION+'LAYER_NAME', 'prova')
        
        # Get field alias
        self.field_alias = []
        for i in range(0, self.TOTAL):
            cur_value = self.settings.value(self.SECTION+'FIELD_ALIAS_'+str(i), '')
            self.field_alias.append(cur_value)
         
        # Get field names
        self.field_name = []
        for i in range(0, self.TOTAL):
            cur_value = self.settings.value(self.SECTION+'FIELD_NAME_'+str(i), '')
            self.field_name.append(cur_value)
        
        # Get default zoom scale
        self.defaultZoomScale = self.settings.value('status/defaultZoomScale', 2500)
        
    
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SelectTrees', message)


    def add_action(self, icon_path, text, callback, parent=None, enabled_flag=True, add_to_menu=True,
        add_to_toolbar=True, status_tip=None, whats_this=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action
        

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        print "initGui"
        icon_path = ':/plugins/SelectTrees/icon_selecttrees.png'
        self.add_action(icon_path, self.tr(u'Selecció arbres'), self.run, self.iface.mainWindow())

        # Create the dock widget and dock it but hide it waiting the end of qgis loading
        self.dlg = SelectTreesDockWidget(self.iface.mainWindow())
        self.iface.mainWindow().addDockWidget(Qt.LeftDockWidgetArea, self.dlg)
        self.dlg.setVisible(False)
        
        # Check if layer exists
        if not self.checkLayer():
            print "Error getting layer of trees"
            return 
            
        # Populate our GUI
        self.populateGui()
        
        # Set signals for each combo
        for i in range(0, self.TOTAL):       
            combo = self.dlg.findChild(QComboBox, "cboField"+str(i))     
            combo.currentIndexChanged.connect(self.performSelect)
    
    
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&SelectTrees'), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
        if self.dlg:
            self.dlg.deleteLater()
            del self.dlg
   
    
    def checkLayer(self):
    
        if self.layer is not None:
            print "Layer already set"
            return True
            
        layers = self.iface.mapCanvas().layers()
        for cur_layer in layers:
            if cur_layer.name() == self.layer_name:
                self.layer = cur_layer
                return self.iface.setActiveLayer(self.layer)
        
        return False
            

    def populateGui(self):
        ''' Populate the interface with values get from active layer
        '''       
        
        print "populateGui"          

        # Load labels
        for i in range(0, self.TOTAL):             
            label = self.dlg.findChild(QLabel, "lblField"+str(i))       
            label.setText(self.field_alias[i])
                    
        # Load combos
        for i in range(0, self.TOTAL):       
            values = set()
            field_name = self.field_name[i]
            for feature in self.layer.getFeatures():
                if type(feature[field_name]) is not QPyNullVariant:
                    values.add(feature[field_name])
            combo = self.dlg.findChild(QComboBox, "cboField"+str(i))
            combo.blockSignals(True)
            combo.clear()
            combo.addItem('')            
            for elem in sorted(values):    
                if type(elem) is int:
                    elem = str(elem)
                combo.addItem(elem)
            combo.blockSignals(False)      

        # TODO: Test
        self.run()
          
    
    def run(self):
        """Run method activated by the toolbar action button"""      

        # Not working: Try to set plugin to left dock widget area by default
        #self.iface.mainWindow().addDockWidget(Qt.LeftDockWidgetArea, self.dlg)
        
        # Get layer tree
        if not self.checkLayer():
            print "Error getting layer"    
            return                 
        
        if self.dlg and not self.dlg.isVisible():  
            # check if the plugin is active
            if not self.pluginName in active_plugins:
                pass
                
        self.dlg.show() 
        
        
    # Signals
    def performSelect(self):

        # Get signal emitter
        emitter = self.sender()
        emitter_name = emitter.objectName()
        combo = self.dlg.findChild(QComboBox, emitter_name)  
        num = int(emitter_name[-1:])

        # Get current text from emitter combo
        value = combo.currentText()
    
        # Get id's from selected features
        selIds = self.layer.selectedFeaturesIds()
        
        
        # Build new expression
        field_name = self.field_name[num]
        aux = field_name+" = '"+value+"'"
        print aux
        
        expr = QgsExpression(aux)
        if expr.hasParserError():
            print exp.parserErrorString()
            return
        
        # Get feature id's that match this expression
        it = self.layer.getFeatures(QgsFeatureRequest(expr))
        newIds = [i.id() for i in it]
        
        # TODO: Check if selection is empty
        #if selection == empty:
        #    select_trees_dockwidget
        #else:
            # Get only those that are already selected and match the expression
            #idsToSel = list(set(selIds).intersection(newIds))
            
        idsToSel = list(set(selIds).intersection(newIds))            
        
        # Select them:            
        self.layer.setSelectedFeatures(idsToSel)    
        
            
