__author__ = 'keyz'
from os import path, makedirs, unlink
from config import TILE_PATH
from metatile_pb2 import Metatile

METATILE_SIZE = 8

'''
Assembles the metatile path and checks if it exists.
If it does not, it ensures all the directories leading to it are created.
'''
def get_and_create_tile_path(style, z, x, y):
    mx, my = get_metatile_coords(x,y)
    tiledir = path.join(TILE_PATH, style, str(z), str(mx))
    if not path.exists(tiledir):
        makedirs(tiledir)
    return path.join(tiledir, str(my) + '.png')


'''
Gets the top-left coords of the metatile that the specified tile is within
'''
def get_metatile_coords(x,y):
    mx = (x//METATILE_SIZE)*METATILE_SIZE
    my = (y//METATILE_SIZE)*METATILE_SIZE
    return (mx,my)

'''
Does the tiles metatile exist
'''
def check_tile(style,z,x,y):
    z = int(z)
    x = int(x)
    y = int(y)
    filename = get_and_create_tile_path(style,z,x,y)
    if path.exists(filename):
        return True
    return False


'''
Tries to read in a tile from a metatile.
If it can't, assume the metatile is bad and delete it
'''
def try_fetch_tile(style,z,x,y):
    z = int(z)
    x = int(x)
    y = int(y)
    filename = get_and_create_tile_path(style,z,x,y)
    if path.exists(filename):
        row = x % METATILE_SIZE
        col = y % METATILE_SIZE

        print("Tile at row:{0} col:{1}".format(row,col))

        tilenum = (METATILE_SIZE * col) + row

        print("Tile num:{0}".format(tilenum))
        try:
            with open(filename,'rb') as file:
                m = Metatile()
                m.ParseFromString(file.read())
                return m.tiles[tilenum].tile
        except:
            print("Couldn't read tile, discarding")
            unlink(filename)
    return None
