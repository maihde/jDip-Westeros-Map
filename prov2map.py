#!/usr/bin/env python
import sys
from xml.etree.ElementTree import ElementTree

tree = ElementTree()
tree.parse(sys.argv[1])

prov = {}
scs = {}
labels = {}
for layer in tree.findall("{http://www.w3.org/2000/svg}g"):
    if layer.attrib["id"] == "UNITS":
        for r in layer.findall("{http://www.w3.org/2000/svg}rect"):
            u = {}
            u['name'] = r.attrib["id"].lower()
            u['x'] = int(float(r.attrib['x'])) + 20
            u['y'] = int(float(r.attrib['y'])) + 20
            u['xd'] = u['x'] - 20 
            u['yd'] =  u['y'] - 20 
            if prov.has_key(u['name']):
                print "ERROR", r
            prov[u['name']] = u
    elif layer.attrib["id"] == "SC":
        for r in layer.findall("{http://www.w3.org/2000/svg}rect"):
            u = {}
            u['name'] = r.attrib["id"][:-3].lower()
            u['x'] = int(float(r.attrib['x'])) + 10
            u['y'] = int(float(r.attrib['y'])) + 10
            if scs.has_key(u['name']):
                print "ERROR", r
            scs[u['name']] = u
    elif layer.attrib["id"] == "LABELS":
        for r in layer.findall("{http://www.w3.org/2000/svg}text"):
            u = {}
            u['id'] = "brf_" + r.text.lower()
            u['name'] = r.text.upper()
            u['x'] = int(float(r.attrib['x']))
            u['y'] = int(float(r.attrib['y']))
            labels[u['id']] = u

keys = prov.keys()
keys.sort()
for k in keys:
    u = prov[k]
    if not labels.has_key("brf_"+k):
        print "Missing Label", k
    if scs.has_key(k):
        sc = scs[k]
        v = (k, u['x'], u['y'], u['xd'], u['yd'], sc['x'], sc['y'])
        print '<jdipNS:PROVINCE name="%s"><jdipNS:UNIT x="%s" y="%s"/><jdipNS:DISLODGED_UNIT x="%s" y="%s"/><jdipNS:SUPPLY_CENTER x="%s" y="%s"/></jdipNS:PROVINCE>' % v
    else:
        v = (k, u['x'], u['y'], u['xd'], u['yd'])
        print '<jdipNS:PROVINCE name="%s"><jdipNS:UNIT x="%s" y="%s"/><jdipNS:DISLODGED_UNIT x="%s" y="%s"/></jdipNS:PROVINCE>' % v

keys = labels.keys()
keys.sort()
for k in keys:
    u  = labels[k]
    print '<text id="%(id)s" x="%(x)s" y="%(y)s">%(name)s</text>' % u
print len(prov), " - Provinces Defined"
print len(scs), " - Supply Centers Defined"
print len(labels), " - Labels Defined"
