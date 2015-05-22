__author__ = 'keyz'
from io import BytesIO
import StringIO
import datetime
import time
from os import path
from celery import Celery
from celery.utils.log import get_task_logger
import redis
from PIL import Image
import mapnik
import math


from metatile_pb2 import Metatile
from utils import get_metatile_coords, get_and_create_tile_path

from config import REDIS_LOCK_URL, REDIS_CELERY_URL, MAPS, TILE_SIZE

METATILE_SIZE = 8

celery = Celery('tasks', backend='redis', broker=REDIS_CELERY_URL)

logger = get_task_logger(__name__)

redis_client = redis.StrictRedis.from_url(REDIS_LOCK_URL)

mapnik.logger.set_severity(mapnik.severity_type.Debug)
mapnik.logger.use_console()


'''
Get the lat/long for the sepcified tile
'''
def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


'''
Render the metatile using the style specified
'''
def render_tile(style, z, x, y):
    z = int(z)
    x, y = get_metatile_coords(x, y)

    logger.info("Rendering metatile: ({0}/{1}/{2})".format(z,x,y))

    #Grab the style's path from the config array
    stylepath = [i for i in MAPS if i[0] == style][0][1]

    south = None
    east = None

    image_size = None

    #For Metatiles < z=3, the size of ALL tiles is <= a single metatile, so we need to take that into account.
    #There's probably some fancy mathsy way to do this, but this'll do for now
    #I'll need to figure out that "fancy mathsy way" if I want configurable metatile sizes
    if z == 0:
        north, west = num2deg(x, y, z)
        south, east = num2deg(x + 1, y + 1, z)
        image_size = TILE_SIZE
    elif z == 1:
        north, west = num2deg(x, y, z)
        south, east = num2deg(x + 2, y + 2, z)
        image_size = TILE_SIZE * 2
    elif z == 2:
        north, west = num2deg(x, y, z)
        south, east = num2deg(x + 4, y + 4, z)
        image_size = TILE_SIZE * 4
    else:
        north, west = num2deg(x, y, z)
        south, east = num2deg(x + 8, y + 8, z)
        image_size = TILE_SIZE * 8

    #Debug info
    start = time.time()

    mn = mapnik.Map(image_size, image_size)
    #Will need to handle this better probably
    try:
        mapnik.load_map(mn, stylepath, True)
    except Exception as e:
        print(e)
        return None

    prj = mapnik.Projection(mn.srs)

    c0 = prj.forward(mapnik.Coord(west, south))
    c1 = prj.forward(mapnik.Coord(east, north))
    bbox = mapnik.Box2d(c0.x, c0.y, c1.x, c1.y)

    mn.zoom_to_box(bbox)
    mn.buffer_size = 128

    im = mapnik.Image(image_size, image_size)

    #More Debug info
    mnimg = time.time()
    mapnik.render(mn, im)

    #TODO: Get this from config
    #We don't want a file, so render to "string" - Actually binary, just using str as a container
    s = im.tostring('png256:c=32:z=9:t=0:m=o')

    #More Debug info
    mnrender = time.time()

    logger.info("Total Time : {}".format(str(datetime.timedelta(seconds=(mnrender - start)))))
    logger.info("Img Time   : {}".format(str(datetime.timedelta(seconds=(mnimg - start)))))
    logger.info("Render Time: {}".format(str(datetime.timedelta(seconds=(mnrender - mnimg)))))
    return s


'''
Split the metatile up into tiles.
Start at top left, then move left to right, top to bottom.
'''
def split_tile(tile):
    #Stick the tile data in a stream so that PIL/Pillow can read it
    stream = BytesIO(tile)
    img = Image.open(stream)

    #Init a new metatile
    metatile = Metatile()
    metatile.size = METATILE_SIZE
    metatile.format = 'PNG'

    #Loop through all tile positions
    for my in range(0, METATILE_SIZE):
        for mx in range(0, METATILE_SIZE):
            #Construct the bounding box of the tile, top left coord, and bottom right
            top = my * TILE_SIZE
            bottom = (my + 1) * TILE_SIZE
            left = mx * TILE_SIZE
            right = (mx + 1) * TILE_SIZE

            bbox = (left, top, right, bottom)

            #Crop to bbox, add a tile to the metatile obj, save the tile to a stream, and save to the metatile
            tiledata = img.crop(bbox)
            tile = metatile.tiles.add()
            tilestream = StringIO.StringIO()
            tiledata.save(tilestream, format='PNG')

            tile.tile = tilestream.getvalue()

    #Again, not really a string, just using str as a container
    return metatile.SerializeToString()


'''
The Celery render task.
Uses redis locks to ensure only one render task is running per metatile.
If the metatile exists, return without rendering.
'''
@celery.task#(base=OneTimeTileRenderTask)
def render_tile_to_file(style=None, z=None, x=None, y=None):
    mx, my = get_metatile_coords(x, y)
    key = "{0}-{1}-{2}-{3}".format(style, z, mx, my)

    # Grab a redis lock, lock until tile is rendered
    with redis_client.lock(key, timeout=60):
        filename = get_and_create_tile_path(style, z, x, y)
        logger.info("Checing or rendering to: {0}".format(filename))

        # if the file exists, assume it's been rendered, and return
        if path.exists(filename):
            logger.info("Tile exists: {0}".format(filename))
            return filename

        # if the file doesn't exist, render it
        with open(filename, 'wb') as file:
            render = render_tile(style, z, x, y)
            metatile = split_tile(render)
            file.write(metatile)

        return filename
