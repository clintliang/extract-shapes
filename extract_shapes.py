import sys
import json
import zipfile
from osgeo import ogr
from osgeo.osr import SpatialReference
from osgeo.osr import CoordinateTransformation
import xml.dom.minidom
from xml.dom.minidom import Node
import mimetypes
import os.path
#from osgeo.ogr import SpatialReference

if len(sys.argv) < 2:
    sys.exit(2)
shapeFile = sys.argv[1]
ext = os.path.splitext(shapeFile)[1]
ds = ogr.Open(shapeFile)
if ds is None:
    sys.exit(3)

toRef = SpatialReference()
toRef.ImportFromEPSG(4326)

data = []
shapes = []

for i in range(ds.GetLayerCount()):
    lyr = ds.GetLayer(i)
    lyr.ResetReading()
    layerName = lyr.GetName()

    #print lyr.GetGeometryColumn()

    fromRef = lyr.GetSpatialRef()
    if fromRef is None:
        sys.exit(4)

    coordTransform = CoordinateTransformation(fromRef, toRef)
    numFeatures = lyr.GetFeatureCount()
    feat = lyr.GetNextFeature()
    if numFeatures==1:
        row = {}
        geom = feat.GetGeometryRef()
        if ext=='.gpx':
            geom=geom.ConvexHull()
        fid = feat.GetFID()

        if geom.IsValid() and geom.IsSimple():
            geom.Transform(coordTransform)

            row['fid'] = feat.GetFID()
            #geom = geom.ConvexHull()
            row['shape'] = geom.ExportToWkt()
            if mimetypes.guess_type(shapeFile)[0]=='application/vnd.google-earth.kml+xml':
                doc = xml.dom.minidom.parse(shapeFile)
                for node in doc.getElementsByTagName("SimpleData"):
                    row[node.getAttribute("name")] = node.childNodes[0].nodeValue
            else:
                for j in range(feat.GetFieldCount()):
                    row[feat.GetFieldDefnRef(j).GetNameRef()] =  feat.GetFieldAsString(j)
            data.append(row)

    elif numFeatures>1 and layerName!="route_points" and layerName!="track_points" and layerName!="routes" and layerName!="waypoints":
        #print layerName+" numFeatures="+str(numFeatures)
        union = None
        while feat is not None:
            #print "---------------------------"+feat.GetDefnRef().GetName()
            row = {}
            geom = feat.GetGeometryRef()
            if geom.IsValid(): #and geom.IsSimple():
                geom.Transform(coordTransform)
                if union is None:
                    union = geom.ConvexHull()
                else:
                    union = union.Union(geom)
            else:
                pass
            feat = lyr.GetNextFeature()
        union = union.ConvexHull()
        row['shape'] = union.ExportToWkt()
        row['title'] = layerName
        row['description'] = layerName
        data.append(row)
print json.dumps(data)
ds.Destroy()
