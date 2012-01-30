#!/usr/bin/env python
# vim: sw=4: et
import sys
import logging
from xml.etree.ElementTree import ElementTree, tostring, dump

logging.basicConfig(stream=sys.stderr)

##############################################################################
# Load the template
template = open("template.svg").read()

##############################################################################
# Parse the map file
mapdata = ElementTree()
mapdata.parse("map.svg")

##############################################################################
# Parse the adjacency file
adjdata = ElementTree()
adjdata.parse("../westeros_adjacency.xml")

EXPECTED_PROVINCES = []
# Use the adjacency data for sanity checking
for prov in adjdata.findall("PROVINCE"):
    EXPECTED_PROVINCES.append(prov.attrib['shortname'])
    for adj in prov.findall("ADJACENCY"):
        if adj.attrib['type'] in ('ec', 'wc', 'nc', 'sc'):
            EXPECTED_PROVINCES.append(prov.attrib['shortname']+"-"+adj.attrib['type'])

EXPECTED_PROVINCES = frozenset(EXPECTED_PROVINCES)

##############################################################################
# Parse the variant file
vardata = ElementTree()
vardata.parse("../variants.xml")

EXPECTED_SUPPLYCENTERS = []
for sc in vardata.findall("VARIANT/SUPPLYCENTER"):
    EXPECTED_SUPPLYCENTERS.append(sc.attrib['province'])
EXPECTED_SUPPLYCENTERS = frozenset(EXPECTED_SUPPLYCENTERS)

##############################################################################
# The data structure to fill in
jdip = {"PROVINCE_DATA": [],
        "MAP_LAYER": [],
        "LABEL_LAYER": [],
        "MOUSE_LAYER": []}

##############################################################################
# Process the map data
provinces = {}
supply_centers = {}
labels = {}
mouse_areas = {}
map_layer = {}
for layer in mapdata.findall("{http://www.w3.org/2000/svg}g"):
    ##########################################################################
    # UNITS LAYER
    if layer.attrib["id"] == "UNITS":
        for r in layer.findall("{http://www.w3.org/2000/svg}rect"): # Unit areas are placed as rectangles
            p = {}
            p['name'] = r.attrib["id"].lower()
            p['x'] = int(float(r.attrib['x'])) + 20 # SVG defines the rectangle in upper-left, jdip expects center-point
            p['y'] = int(float(r.attrib['y'])) + 20
            p['xd'] = p['x'] - 20 
            p['yd'] =  p['y'] - 20 
            if provinces.has_key(p['name']):
                logging.error("Duplicate province '%s' defined", p['name'])
                sys.exit(-1)
            provinces[p['name']] = p
    ##########################################################################
    # SC LAYER
    elif layer.attrib["id"] == "SC":
        for r in layer.findall("{http://www.w3.org/2000/svg}rect"):
            sc = {}
            sc['name'] = r.attrib["id"][:-3].lower()
            sc['x'] = int(float(r.attrib['x'])) + 10 # SVG defines the rectangle in scpper-left, jdip expects center-point
            sc['y'] = int(float(r.attrib['y'])) + 10
            if supply_centers.has_key(sc['name']):
                logging.error("Duplicate supply center '%s' defined", sc['name'])
                sys.exit(-1)
            supply_centers[sc['name']] = sc
    ##########################################################################
    # LABEL LAYER
    elif layer.attrib["id"] == "LABELS":
        for t in layer.findall("{http://www.w3.org/2000/svg}text"):
            l = {}
            if not t.attrib['id'].startswith("brf_"):
                logging.error("Label id '%s' must start with 'brf_'", t.attrib['id'])
                sys.exit(-1)
            l['id'] = t.attrib['id'][4:]
            l['name'] = t.text.upper()
            l['class'] = t.attrib['class']
            l['x'] = int(float(t.attrib['x']))
            l['y'] = int(float(t.attrib['y']))
            if labels.has_key(l['id']):
                logging.error("Duplicate label '%s' defined", l['id'])
                sys.exit(-1)
            labels[l['id']] = l
    ##########################################################################
    # MAP LAYER
    elif layer.attrib["id"] == "MapLayer":
        for p in layer.findall("{http://www.w3.org/2000/svg}path"):
            m = {}
            m['id'] = p.attrib['id']
            m['d'] = p.attrib['d']
            m['class'] = p.attrib['class']
            if map_layer.has_key(m['id']):
                logging.error("Duplicate map-area '%s' defined", m['id'])
                sys.exit(-1)
            map_layer[m['id']] = m

    ##########################################################################
    # MOUSE LAYER
    elif layer.attrib["id"] == "MouseLayer":
        for p in layer.findall("{http://www.w3.org/2000/svg}path"):
            m = {}
            m['id'] = p.attrib['id']
            m['d'] = p.attrib['d']
            if mouse_areas.has_key(m['id']):
                logging.error("Duplicate mouse-area '%s' defined", m['id'])
                sys.exit(-1)
            mouse_areas[m['id']] = m


##############################################################################
# Validate the data
DEFINED_PROVINCES = frozenset(provinces.keys())
if len(DEFINED_PROVINCES - EXPECTED_PROVINCES) > 0:
    extra = DEFINED_PROVINCES - EXPECTED_PROVINCES
    logging.error("Extra provinces: %s", extra)
    sys.exit(-1)
if len(EXPECTED_PROVINCES - DEFINED_PROVINCES) > 0:
    missing = EXPECTED_PROVINCES - DEFINED_PROVINCES 
    logging.error("Missing provinces: %s", missing)
    sys.exit(-1)
   
DEFINED_LABELS = frozenset(labels.keys())
if len(EXPECTED_PROVINCES - DEFINED_LABELS) > 0 :
    missing = EXPECTED_PROVINCES - DEFINED_LABELS 
    logging.error("Missing labels: %s", missing)
    sys.exit(-1)

DEFINED_MOUSEAREAS = frozenset(mouse_areas.keys())
if len(DEFINED_MOUSEAREAS - EXPECTED_PROVINCES) > 0:
    extra = DEFINED_MOUSEAREAS - EXPECTED_PROVINCES
    logging.error("Extra mouse areas: %s", extra)
    sys.exit(-1)
if len(EXPECTED_PROVINCES - DEFINED_MOUSEAREAS) > 0 :
    missing = EXPECTED_PROVINCES - DEFINED_MOUSEAREAS
    logging.error("Missing mouse areas: %s", missing)
    sys.exit(-1)

DEFINED_SUPPLYCENTERS = frozenset(supply_centers.keys())
if len(DEFINED_SUPPLYCENTERS - EXPECTED_SUPPLYCENTERS) > 0:
    extra = DEFINED_SUPPLYCENTERS - EXPECTED_SUPPLYCENTERS
    logging.error("Extra supply centers: %s", extra)
    sys.exit(-1)
if len(EXPECTED_SUPPLYCENTERS - DEFINED_SUPPLYCENTERS) > 0: 
    missing = EXPECTED_SUPPLYCENTERS - DEFINED_SUPPLYCENTERS 
    logging.error("Missing supply centers: %s", missing)
    sys.exit(-1)

##############################################################################
# Format the output
sorted_provinces = provinces.keys()
sorted_provinces.sort()
for name in sorted_provinces:
    p = provinces[name]
    # Determine if the province has a supply center or not
    if supply_centers.has_key(name):
        sc = supply_centers[name]
        v = (name, p['x'], p['y'], p['xd'], p['yd'], sc['x'], sc['y'])
        jdip['PROVINCE_DATA'].append('    <jdipNS:PROVINCE name="%s"><jdipNS:UNIT x="%s" y="%s"/><jdipNS:DISLODGED_UNIT x="%s" y="%s"/><jdipNS:SUPPLY_CENTER x="%s" y="%s"/></jdipNS:PROVINCE>' % v)
    else:
        v = (name, p['x'], p['y'], p['xd'], p['yd'])
        jdip['PROVINCE_DATA'].append('    <jdipNS:PROVINCE name="%s"><jdipNS:UNIT x="%s" y="%s"/><jdipNS:DISLODGED_UNIT x="%s" y="%s"/></jdipNS:PROVINCE>' % v)

sorted_labels = labels.keys()
sorted_labels.sort()
for name in sorted_labels:
    l = labels[name]
    jdip['LABEL_LAYER'].append('    <text id="%(id)s" class="%(class)s" x="%(x)s" y="%(y)s">%(name)s</text>' % l)

sorted_mouse_areas = mouse_areas.keys()
sorted_mouse_areas.sort()
for name in sorted_mouse_areas:
    m = mouse_areas[name]
    jdip['MOUSE_LAYER'].append('    <path id="%(id)s" d="%(d)s"/>' % m)

sorted_map_paths = map_layer.keys()
sorted_map_paths.sort()
for name in sorted_map_paths:
    m = map_layer[name]
    jdip['MAP_LAYER'].append('    <path id="%(id)s" class="%(class)s" d="%(d)s"/>' % m)

jdip['PROVINCE_DATA'] = "\n".join(jdip['PROVINCE_DATA'])
jdip['LABEL_LAYER'] = "\n".join(jdip['LABEL_LAYER'])
jdip['MOUSE_LAYER'] = "\n".join(jdip['MOUSE_LAYER'])
jdip['MAP_LAYER'] = "\n".join(jdip['MAP_LAYER'])

##############################################################################
# Write the output
if len(sys.argv) == 1:
    output = sys.stdout
else:
    output = open(sys.argv[1], "w")
output.write(template % jdip)
