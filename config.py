__author__ = 'keyz'

DEBUG=True

TILE_PATH='/tmp/tiles'
TILE_SIZE=256

REDIS_LOCK_URL='redis://localhost:6379/2'
REDIS_CELERY_URL='redis://localhost:6379/3'

MAPS = [
    ('osmbright','maps/OSMBright/osmbright.xml')
]