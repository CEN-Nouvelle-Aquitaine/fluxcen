# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FluxCEN
                                 A QGIS plugin
 Flux IGN etc etc
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-04-04
        copyright            : (C) 2022 by Romain Montillet
        email                : r.montillet@cen-na.org
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
    """Load FluxCEN class from file FluxCEN.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .FluxCEN import FluxCEN
    return FluxCEN(iface)
