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

from lxml import etree
import os

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

basedir = os.getcwd()
wed_file = etree.parse (os.path.join (basedir,"earth.wed.xml"))
wed_objs = wed_file.getroot() [0] # now we take into account only objects, without prefs

taxinodes = []
idtaxinodes = []

#find LinearFeatures with Solid Yellow
parents = []
for obj in wed_objs:
    for mrks in obj:
        if mrks.tag == "markings":
            for mrk in mrks:
                if (mrk.get ("value") == "Solid Yellow"):
                    if obj.get("parent_id") not in parents: parents.append (obj.get("parent_id"))

#find points
points =[]
twyseg = []
for obj in wed_objs:
    if obj.get ("id") in parents:
        for src in obj:
            if src.tag == ("sources"):
                segment = []
                for child in src:
                    if child.tag == "child":
                        childID = child.get ("id")
                        points.append (childID)
                        segment.append (childID)
                for s in range (len (segment) - 1):
                    twyseg.append ([segment [s], segment [s+1], obj.get ("id")])

#make point list
for obj in wed_objs:
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

#Save
file_groundnet = open (os.path.join (basedir,  "newGroundNet.xml"), "w")
file_groundnet.writelines( "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + "\r\n")
file_groundnet.writelines( "<groundnet>" + "\r\n")
file_groundnet.writelines( "  <TaxiNodes>" + "\r\n")
                
for line in taxinodes: file_groundnet.writelines('    <node index="' + line[0] + '" lat="' + latNS (line[1]) + '" lon="' + lonEW(line[2]) + '" isOnRunway="0" holdPointType="none" />' + "\r\n")
file_groundnet.writelines( "  </TaxiNodes>" + "\r\n")
file_groundnet.writelines( "  <TaxiWaySegments>" + "\r\n")
for line in twyseg:
    file_groundnet.writelines('    <arc begin="' + line[0] + '" end="' + line[1] + '" isPushBackRoute="0" name="' + line[2] + '" />' + "\r\n")
    file_groundnet.writelines('    <arc begin="' + line[1] + '" end="' + line[0] + '" isPushBackRoute="0" name="' + line[2] + '" />' + "\r\n")
file_groundnet.writelines( "  </TaxiWaySegments>" + "\r\n")
file_groundnet.writelines( "</groundnet>")
file_groundnet.close()
