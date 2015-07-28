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
from qgis.utils import active_plugins
from qgis.gui import (QgsMessageBar, QgsTextAnnotationItem)
from qgis.core import (QgsGeometry, QgsPoint, QgsLogger, QgsExpression, QgsFeatureRequest, QgsMessageLog, QgsVectorFileWriter, QgsVectorLayer, QgsFeature, QgsMapLayerRegistry)
from PyQt4.QtCore import (QObject, QSettings, QTranslator, qVersion, QCoreApplication, Qt, pyqtSignal, QPyNullVariant)
from PyQt4.QtGui import (QAction, QIcon, QDockWidget, QTextDocument, QIntValidator, QLabel, QComboBox, QPushButton)

# Initialize Qt resources from file resources.py
import resources_rc

# Import the code for the dialog
from select_trees_dockwidget import SelectTreesDockWidget
import os.path

import sys  
#reload(sys)  
#sys.setdefaultencoding('utf8')


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
        self.mem_layer = None          
        self.layer = None  
        self.initialize = False
        
        # establish connection when all is completely running 
        self.iface.initializationCompleted.connect(self.populateGui)

    
    def loadPluginSettings(self):
        ''' Load plugin settings
        '''       
        # Get main credentials
        self.TOTAL = 6
        self.SECTION = "main/"
        
        # Get layer name
        self.layer_name = self.settings.value(self.SECTION+'LAYER_NAME', 'Arbres')
        self.mem_layer_name = self.settings.value(self.SECTION+'MEM_LAYER_NAME', 'Arbres seleccionats')
        
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
        self.minZoomScale = int(self.settings.value('status/minZoomScale', 500))
        
        # Get path to QML file
        self.path_qml = self.settings.value(self.SECTION+'PATH_QML', 'styles/arbres.qml') 
        self.path_qml = self.plugin_dir+"/"+self.path_qml
        if not os.path.exists(self.path_qml):
            print self.path_qml
            QgsMessageLog.logMessage(u"QML file not found at: "+self.path_qml, "selectTrees", QgsMessageLog.WARNING)            
        
    
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


    def add_action(self, icon_path, text, callback, parent, shortcut=None,
        enabled_flag=True, add_to_menu=True, add_to_toolbar=False, status_tip=None, whats_this=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if shortcut is not None:
            self.iface.registerMainWindowAction(action, shortcut)         

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)
        else:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action
        
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SelectTrees/icon_selecttrees.png'
        self.add_action(icon_path, self.tr(u'Selecció arbres'), self.run, self.iface.mainWindow(), "F8")       

        # Create the dock widget and dock it but hide it waiting the end of qgis loading
        self.dlg = SelectTreesDockWidget(self.iface.mainWindow())
        self.iface.mainWindow().addDockWidget(Qt.LeftDockWidgetArea, self.dlg)
        self.dlg.setVisible(False)
        
        # Set signals
        self.dlg.findChild(QPushButton, "btnReset").clicked.connect(self.reset)
        btnZoom = self.dlg.findChild(QPushButton, "btnZoom")
        if btnZoom:
            btnZoom.clicked.connect(self.zoom)        
        for i in range(0, self.TOTAL):       
            combo = self.dlg.findChild(QComboBox, "cboField"+str(i))     
            combo.currentIndexChanged.connect(self.performSelect)
    
    
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&SelectTrees'), action)
            self.iface.removeToolBarIcon(action)
        
        if self.dlg:
            self.dlg.deleteLater()
            del self.dlg
   
    
    def checkLayer(self):
    
        if self.layer is not None:
            return self.iface.setActiveLayer(self.layer)
           
        # Iterate over all layers to get the one set in config file
        layers = self.iface.mapCanvas().layers()
        for cur_layer in layers:
            if cur_layer.name() == self.layer_name:
                self.layer = cur_layer
                self.feature_count = self.layer.featureCount()           
                return self.iface.setActiveLayer(self.layer)
            if cur_layer.name() == self.mem_layer_name:
                self.mem_layer = cur_layer
        
        return False
            

    def populateGui(self):
        ''' Populate the interface with values get from active layer
        '''           
        #QgsMessageLog.logMessage(u"populateGui: init", "selectTrees", QgsMessageLog.INFO)
        
        # Check if layer exists
        if not self.checkLayer():
            QgsMessageLog.logMessage(u"populateGui: Error getting layer of trees", "selectTrees", QgsMessageLog.INFO)
            self.iface.mainWindow().removeDockWidget(self.dlg)          
            return 
            
        # Get counter label
        self.lblCountSelect = self.dlg.findChild(QLabel, "lblCountSelect")  
                
        # Load field labels
        for i in range(0, self.TOTAL):             
            label = self.dlg.findChild(QLabel, "lblField"+str(i))       
            label.setText(self.field_alias[i])
                    
        # Load field combos
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
                if type(elem) is int or type(elem) is long:
                    elem = str(elem)
                combo.addItem(elem)
            combo.blockSignals(False)      

        # Update counter
        self.updateCounter()
        
        self.initialize = True
        

    def updateCounter(self):
        
        msg = "Seleccionats "+str(self.layer.selectedFeatureCount())+" de "+str(self.feature_count)+" arbres"    
        self.lblCountSelect.setText(msg)        
          
    
    def run(self):
        """Run method activated by the toolbar action button"""      
        
        if not self.initialize:
            self.populateGui()
        else:  
            # Get layer set in config file
            if not self.checkLayer():
                self.dlg.setVisible(False)
                return                 
        
        if self.dlg and not self.dlg.isVisible():  
            # check if the plugin is active
            if not self.pluginName in active_plugins:
                pass
               
        # Not working: Try to set plugin to left dock widget area by default               
        self.iface.mainWindow().addDockWidget(Qt.LeftDockWidgetArea, self.dlg)                
        self.dlg.show() 
        
        
    def deleteFeatures(self, layer):
    
        it = layer.getFeatures()
        ids = [i.id() for i in it]
        layer.dataProvider().deleteFeatures(ids)    
    
    
    # Copy from Arbres to memory layer
    def copySelected(self):
    
        # Create memory layer if not already set
        if self.mem_layer is None:       
            uri = "Point?crs=epsg:25831"        
            self.mem_layer = QgsVectorLayer(uri, self.mem_layer_name, "memory")  
            self.mem_layer.loadNamedStyle(self.path_qml)            
            QgsMapLayerRegistry.instance().addMapLayer(self.mem_layer)                

        # Prepare point layer for editing
        self.mem_layer.startEditing()

        # Delete previous features
        self.deleteFeatures(self.mem_layer)
        
        # Iterate over selected features
        for sel_feature in self.layer.selectedFeatures():
            feature = QgsFeature()
            feature.setGeometry(sel_feature.geometry())        
            self.mem_layer.addFeature(feature, True)
          
        # Commit and refresh canvas
        self.mem_layer.commitChanges()
        self.iface.mapCanvas().refresh()        

        
    # Signals
    def performSelect(self):

        # Get values from every combo
        expr_list = []
        for i in range(0, self.TOTAL):   
            combo = self.dlg.findChild(QComboBox, "cboField"+str(i))  
            value = combo.currentText()
            if value != '':
                field_name = self.field_name[i]
                value = value.replace("'", "\\'")
                aux = field_name+" = '"+value+"'"       
                expr_list.append(aux)
    
        # Build new expression
        aux = ''
        for i in range(len(expr_list)):
            if aux != '':
                aux+= ' and '
            aux+= expr_list[i]
        expr = QgsExpression(aux)
        if expr.hasParserError():
            QgsMessageLog.logMessage(expr.parserErrorString() + ": " + aux, "selectTrees", QgsMessageLog.INFO)  
            return      
        
        # Get a featureIterator from an expression
        # Build a list of feature Ids from the previous result       
        # Select features with the ids obtained
        it = self.layer.getFeatures(QgsFeatureRequest(expr))
        ids = [i.id() for i in it]
        self.layer.setSelectedFeatures(ids)
        
        # Update counter
        self.updateCounter()
        
        # Copy selected features to memory layer
        self.copySelected()
    
    
    def reset(self):
    
        # Reset combos, remove selection and update counter
        for i in range(0, self.TOTAL):   
            combo = self.dlg.findChild(QComboBox, "cboField"+str(i))  
            combo.blockSignals(True)                
            combo.setCurrentIndex(0)
            combo.blockSignals(False)                
        self.layer.removeSelection()
        self.deleteFeatures(self.mem_layer)    
        self.updateCounter()        
        self.iface.mapCanvas().refresh()

    
    def zoom(self):
  
        if self.checkLayer():
            action = self.iface.actionZoomToSelected()
            action.trigger()
            if self.iface.mapCanvas().scale() < self.minZoomScale:
                self.iface.mapCanvas().zoomScale(self.minZoomScale)
        
            
