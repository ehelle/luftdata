import requests
import re
import shapely.wkt
import json
from shapely.geometry import shape, GeometryCollection
from functools import lru_cache

def getJson(url):
    return requests.get(url).json()

def wkt2line(wkt):
    simpledec = re.compile(r"-?\d+\.\d+")
    wkt = re.sub(simpledec, mround, wkt)
    line = shapely.wkt.loads(wkt)
    #if hasMissingZ(wkt): # transform to NaN at later stage.
        #line = shapely.ops.transform(_to_2d, line)
    return line

def getTrafikkmengde(id):
    url = 'https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/540/{}'.format(id)
    json = getJson(url)
    return json

def geom(obj):
    wkt = obj['geometri']['wkt']
    return wkt2line(wkt)

def geomPunkt(obj, punkt):
    linje = geom(obj)
    punkt = linje.interpolate(punkt, normalized=True)
    return punkt

def mround(match):
    return "{:.2f}".format(float(match.group()))

def geomMidtpunkt(obj):
    return geomPunkt(obj, 0.5)

def punkt2vegkategori(punkt):
    nord = punkt.y
    ost = punkt.x
    url = 'https://nvdbapiles-v3.atlas.vegvesen.no/posisjon?maks_avstand=10&nord={}&ost={}'.format(nord,ost)
    data = getJson(url)
    return data[0]['vegsystemreferanse']['vegsystem']['vegkategori']

@lru_cache(maxsize=None)
def getPopulatedArea():
    with open("kommuner2019_simple.geojson") as f:
        features = json.load(f)["features"]
    geom = GeometryCollection([shape(feature['geometry']).buffer(0)
                               for feature in features
                               if feature['properties']['kommunenummer'] in byKommuner()
                               and feature['geometry'] != None])
    return geom

@lru_cache(maxsize=None)
def byKommuner():
    with open('byKommuner.txt') as lst:
        return lst.read().splitlines()

def isInPopulatedArea(geom):
    populatedArea = getPopulatedArea()
    return geom.within(populatedArea)

def isEuropaveiOrRiksvei(vegkategori):
    return vegkategori in ['E', 'R']

def trafikkmengde2faktorvariasjonskurve(id):
    trafikkmengde = getTrafikkmengde(id)
    midtpunkt = geomMidtpunkt(trafikkmengde)
    vegkategori = punkt2vegkategori(midtpunkt)
    if isInPopulatedArea(midtpunkt):
        letter = 'A'
    else:
        letter = 'B'
    if isEuropaveiOrRiksvei(vegkategori):
        number = '1'
    else:
        number = '2'
    return letter + number
