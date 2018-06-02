# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SortNumber
                                 A QGIS plugin
 This plugin sorts and numbers an attribute table.
                              -------------------
        begin                : 2016-05-03
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Alexandre Delahaye
        email                : menoetios@gmail.com
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
from __future__ import absolute_import
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QObject, QSettings, QTranslator, QVariant, qVersion, QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import *
import qgis.utils
#import locale
# Initialize Qt resources from file resources.py
from . import resources
# Import the code for the dialog
from .sort_number_dialog import SortNumberDialog
import os.path


class SortNumber(QObject):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        super(SortNumber, self).__init__() # necessary for pyqtSignal

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SortNumber_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = SortNumberDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Sort and Number')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SortNumber')
        self.toolbar.setObjectName(u'SortNumber')

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
        return QCoreApplication.translate('SortNumber', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

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
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SortNumber/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Sort & Number'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.dlg.layerComboBox.activated.connect( self.onLayerChange )
        self.dlg.attributeComboBox1.activated.connect( self.onAttr1Change )
        self.dlg.attributeComboBox2.activated.connect( self.onAttr2Change )
        self.dlg.fieldNameLineEdit.textChanged.connect( self.checkRunButton )
        self.dlg.runButton.clicked.connect( self.main )


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Sort and Number'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def onLayerChange(self, index):

        self.excludeList = ["", ""] # selected fields (used to filter comboboxes)

        # if a layer is selectd, fill 1st attribute combobox
        if index > 0:
            self.dlg.attributeComboBox1.setEnabled(True)
            self.disableCheckBoxesFrom( 2 )
            self.dlg.invCheckBox1.setEnabled(True)
            self.layer = self.dlg.layerComboBox.itemData( index )
            self.fillAttrComboBox( self.dlg.attributeComboBox1 )

        # else, disable 1st combobox
        else:
            self.dlg.attributeComboBox1.setEnabled(False)
            self.dlg.attributeComboBox1.clear()
            self.disableCheckBoxesFrom( 1 )

        # disable other comboboxes
        self.dlg.attributeComboBox2.setEnabled(False)
        self.dlg.attributeComboBox2.clear()
        self.dlg.attributeComboBox3.setEnabled(False)
        self.dlg.attributeComboBox3.clear()

        self.checkRunButton()


    def onAttr1Change(self, index):

        # if a field is selected, fill 2nd attribute combobox
        if index > 0:
            self.dlg.attributeComboBox2.setEnabled(True)
            self.disableCheckBoxesFrom( 3 )
            self.dlg.invCheckBox2.setEnabled(True)
            field = self.dlg.attributeComboBox1.itemData( index )

            self.excludeList = [field.name(), ""]
            self.fillAttrComboBox( self.dlg.attributeComboBox2 )

        # else, disable 2nd combobox
        else:
            self.dlg.attributeComboBox2.setEnabled(False)
            self.dlg.attributeComboBox2.clear()
            self.disableCheckBoxesFrom( 2 )
            self.excludeList = ["", ""]

        # disable 3rd comboboxes
        self.dlg.attributeComboBox3.setEnabled(False)
        self.dlg.attributeComboBox3.clear()

        self.checkRunButton()


    def onAttr2Change(self, index):

        # if a field is selected, fill 3rd attribute combobox
        if index > 0:
            self.dlg.attributeComboBox3.setEnabled(True)
            self.dlg.invCheckBox3.setEnabled(True)
            field = self.dlg.attributeComboBox2.itemData( index )

            self.excludeList[1] = field.name()
            self.fillAttrComboBox( self.dlg.attributeComboBox3 )

        # else, disable 3rd combobox
        else:
            self.dlg.attributeComboBox3.setEnabled(False)
            self.dlg.attributeComboBox3.clear()
            self.disableCheckBoxesFrom( 3 )
            self.excludeList[1] = ""


    def fillAttrComboBox(self, comboBox):
        comboBox.clear() # clear the combobox
        comboBox.addItem( '', None ) 
        for field in self.layer.fields():
            if not field.name() in self.excludeList:
                comboBox.addItem( field.name(), field )


    def disableCheckBoxesFrom(self, idx):

        if idx < 2:
            self.dlg.invCheckBox1.setChecked(False)
            self.dlg.invCheckBox1.setEnabled(False)

        if idx < 3:
            self.dlg.invCheckBox2.setChecked(False)
            self.dlg.invCheckBox2.setEnabled(False)

        self.dlg.invCheckBox3.setChecked(False)
        self.dlg.invCheckBox3.setEnabled(False)


    def checkRunButton(self):

        if self.dlg.layerComboBox.currentIndex() > 0 and self.dlg.attributeComboBox1.currentIndex() > 0 and self.dlg.fieldNameLineEdit.text() != "":
            self.dlg.runButton.setEnabled(True)
        else:
            self.dlg.runButton.setEnabled(False)


    def main(self):

        # If attribute already exists
        if not self.layer.dataProvider().fields().indexFromName( self.dlg.fieldNameLineEdit.text() ) == -1:
            messageBox = QMessageBox()
            messageBox.setWindowTitle( "Sort and Number" )
            messageBox.setText( self.tr("Field name already exists!") )
            messageBox.setInformativeText( self.tr("Continue anyway? Existing values will be lost.") )
            messageBox.setIcon( QMessageBox.Warning )
            messageBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel);
            res = messageBox.exec_()

            # Cancel overwrite
            if res == QMessageBox.Cancel:
                # self.dlg.runButton.setEnabled(True)
                # self.dlg.closeButton.setEnabled(True)
                return
            # Continue and overwrite
            else:
                attrIdx = self.layer.dataProvider().fields().indexFromName( self.dlg.fieldNameLineEdit.text() )
                # Reset order values to NULL
                self.layer.startEditing()
                for f in list( self.layer.getFeatures() ):
                    self.layer.changeAttributeValue(f.id(), attrIdx, None)
                self.layer.commitChanges()


        else:
            # Add new attribute
            self.layer.dataProvider().addAttributes( [QgsField(self.dlg.fieldNameLineEdit.text(), QVariant.Int)] )
            attrIdx = self.layer.dataProvider().fields().indexFromName( self.dlg.fieldNameLineEdit.text() )
            self.layer.updateFields() # tell the vector layer to fetch changes from the provider


        self.dlg.runButton.setEnabled(False)

        # Get params
        field1 = self.dlg.attributeComboBox1.itemData( self.dlg.attributeComboBox1.currentIndex() )
        field1Id = self.layer.dataProvider().fields().indexFromName( field1.name() )
        isInv1 = self.dlg.invCheckBox1.isChecked()

        if self.dlg.attributeComboBox2.currentIndex() > 0:
            field2 = self.dlg.attributeComboBox2.itemData( self.dlg.attributeComboBox2.currentIndex() )
            field2Id = self.layer.dataProvider().fields().indexFromName( field2.name() )
            isInv2 = self.dlg.invCheckBox2.isChecked()
        else:
            field2 = None
            field2Id = None

        if self.dlg.attributeComboBox3.currentIndex() > 0:
            field3 = self.dlg.attributeComboBox3.itemData( self.dlg.attributeComboBox3.currentIndex() )
            field3Id = self.layer.dataProvider().fields().indexFromName( field3.name() )
            isInv3 = self.dlg.invCheckBox3.isChecked()
        else:
            field3 = None
            field3Id = None

        #locale.setlocale(locale.LC_ALL, "") # alphabetical sort

        if self.dlg.selFeatureCheckBox.isChecked():
            featureList = list( self.layer.selectedFeatures() )
            # Message to Log Messages Panel for debugging		
            #QgsMessageLog.logMessage( "Use selected features only.", "QGISSortAndNumber", 0 )
        else:
            featureList = list( self.layer.getFeatures() )
            #QgsMessageLog.logMessage( "Use all features.", "QGISSortAndNumber", 0 )

        if field3Id != None:
            featureList = sorted(featureList, key=lambda f: f[field3Id], reverse=isInv3)

        if field2Id != None:
            featureList = sorted(featureList, key=lambda f: f[field2Id], reverse=isInv2)

        featureList = sorted(featureList, key=lambda f: f[field1Id], reverse=isInv1)

        # add numbering field to layer
        self.layer.startEditing()
        
        for i, f in enumerate(featureList):
            #print f.id()
            self.layer.changeAttributeValue(f.id(), attrIdx, i+1)

        self.layer.commitChanges()

        # "Done" message
        messageBox = QMessageBox()
        messageBox.setWindowTitle( "Sort and Number" )
        messageBox.setText( self.tr("Done") )
        messageBox.setIcon( QMessageBox.Information )
        messageBox.setStandardButtons(QMessageBox.Ok);
        res = messageBox.exec_()

        self.dlg.runButton.setEnabled(True)


    def run(self):
        """Run method that performs all the real work"""

        mapCanvas = self.iface.mapCanvas()

        # some elements are disabled by default
        self.disableCheckBoxesFrom( 1 )
        self.dlg.attributeComboBox1.setEnabled(False)
        self.dlg.attributeComboBox1.clear()
        self.dlg.attributeComboBox2.setEnabled(False)
        self.dlg.attributeComboBox2.clear()
        self.dlg.attributeComboBox3.setEnabled(False)
        self.dlg.attributeComboBox3.clear()
        self.dlg.runButton.setEnabled(False)

        # list layers for input combobox
        self.dlg.layerComboBox.clear() # clear the combobox
        self.dlg.layerComboBox.addItem( '', None ) 
        layers = list(QgsProject.instance().mapLayers().values()) # Create list with all layers
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer: # check if layer is vector
                self.dlg.layerComboBox.addItem( layer.name(), layer ) 

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
