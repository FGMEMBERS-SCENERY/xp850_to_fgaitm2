#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       xp850_to_FGAITM2.py
#       
#       Copyright 2012 Vadym Kukhtin <valleo@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


# Convert X-Plane-8.50 yellow lines to FG AI TrafficManagerII groundnet
# Run this script in one folder with earth.wed.xml
# Your groundnet will be newGroundNet.xml
# Add parking places separately by hand.

sortsOfLine = ["Solid Yellow (Black)", "Solid Yellow"]

import xml.etree.ElementTree as ET
import os
from xml.dom.minidom import parseString

def latNS (coord):
    line = ""
    deg = int (coord)
    if coord < 0 : line = "S" + str (deg)
    else: line = "N" + str (deg)
    
    min = coord - int (coord)
    line = line + " " + str ("%.3f" % (60 * min))
    return line

def lonEW (coord):
    line = ""
    deg = int (coord)
    if coord < 0 : line = "W" + str (deg)
    else: line = "E" + str (deg)
    
    min = coord - int (coord)
    line = line + " " + str ("%.3f" % (60 * min))
    return line

taxinodes = []
idtaxinodes = []

#find LinearFeatures with Solid Yellow
parents = []
filexml = ET.parse  ("earth.wed.xml")
doc = filexml.getroot()
objects = doc.find("objects")


for obj in objects:
	for markings in obj.getiterator ("markings"):
		for marking in markings.getiterator ("marking"):
			if marking.attrib["value"] in sortsOfLine:
				parentID = obj.attrib["parent_id"]
				if parentID not in parents:
					parents.append (parentID)

#find points

points =[]
twyseg = []
for obj in objects:
    if obj.get ("id") in parents:
        for src in obj:
            if src.tag == ("children"):
                segment = []
                for child in src:
                    if child.tag == "child":
                        childID = child.get ("id")
                        points.append (childID)
                        segment.append (childID)
                for s in range (len (segment) - 1):
                    twyseg.append ([segment [s], segment [s+1], obj.get ("id")])


#make point list
for obj in objects:
    if obj.get ("id") in points:
        for attr in obj:
            if attr.tag == "point":
                lat = attr.get ("latitude") 
                lon = attr.get ("longitude")
                taxinodes.append ([obj.get ("id"), eval(lat), eval(lon)])

#find points with same coord
PntCln = ()
for p in taxinodes:
    pcoord = (p[1], p[2])
    pid = p[0]
    samePoints = []
    for s in taxinodes:
        scoord = (s[1], s[2])
        sid = s[0]
        if pcoord == scoord and sid <> pid:
            samePoints.append (s)
    # samePoints is list of id of dublicates
    # now we delete dupes from taxinodes, 
    # and change id in twyseg
    if len(samePoints) > 0 :
        for i in samePoints:
            taxinodes.remove (i)
            for t in twyseg:
                if t[0] == i[0]: 
                    t[0] = pid
                if t[1] == i[0]:
                    t[1] = pid

groundnet = ET.Element("groundnet")

TaxiNodes = ET.SubElement (groundnet, "TaxiNodes")
for line in taxinodes:
	node = ET.SubElement(TaxiNodes, "node")
	node.set ("index", line [0])
	node.set ("lat", latNS (line[1]))
	node.set ("lon", lonEW (line[2]))
	node.set ("isOnRunway", "0")
	node.set ("holdPointType", "none")

TaxiWaySegments = ET.SubElement (groundnet, "TaxiWaySegments")
for line in twyseg:
	arc = ET.SubElement (TaxiWaySegments, "arc")
	arc.set ("begin", line[0])
	arc.set ("end", line[1])
	arc.set ("isPushBackRoute", "0")
	arc.set ("name", line[2])
	#reverse arc
	arc = ET.SubElement (TaxiWaySegments, "arc")
	arc.set ("begin", line[1])
	arc.set ("end", line[0])
	arc.set ("isPushBackRoute", "0")
	arc.set ("name", line[2])
	


#Save
basedir = os.getcwd()
file_groundnet = open (os.path.join (basedir,  "newGroundNet.xml"), "w")
txt = ET.tostring (groundnet)
ps = parseString (txt)
file_groundnet.writelines (ps.toprettyxml(indent=" "))
file_groundnet.close()
