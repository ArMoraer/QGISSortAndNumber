# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SortNumber
                                 A QGIS plugin
 This plugin sorts and numbers an attribute table.
                             -------------------
        begin                : 2016-05-03
        copyright            : (C) 2016 by Alexandre Delahaye
        email                : menoetios@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SortNumber class from file SortNumber.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .sort_number import SortNumber
    return SortNumber(iface)
