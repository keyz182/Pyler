__author__ = 'keyz'
from tornado import gen, web, ioloop
from tornado.web import asynchronous
from tornado.httpserver import HTTPServer
from tornado.concurrent import Future, return_future

import tasks
from utils import try_fetch_tile
from config import DEBUG


class TileHandler(web.RequestHandler):
    '''
    Checks if the tile file exists.
    If exists, returns tile data
    If not, executes a render task
    On render task return, go back to start
    '''
    @return_future
    def get_tile(self, style, z, x, y, callback=None):
        tile = None
        ret = None

        while True:
            if ret is not None and ret.ready():
                tile = try_fetch_tile(style, z, x, y)
                if tile:
                    print("Fetching and Sending {0}/{1}/{2}/{3}".format(style, z, x, y))
                    break
            elif ret is None:
                print("Tile not found, rendering {0}/{1}/{2}/{3}".format(style, z, x, y))
                ret = tasks.render_tile_to_file.apply_async(
                    kwargs={'style': style, 'z': int(z), 'x': int(x), 'y': int(y)})

        callback(tile)

    @asynchronous
    @gen.coroutine
    def get(self, style, z, x, y):
        self.set_header('Content-Type', 'image/png; charset="utf-8"')
        tile = yield(self.get_tile(style, z, x, y))
        self.write(tile)
        self.finish()


def make_app():
    return web.Application([
        (r"/([^/]+)/([0-9]+)/([0-9]+)/([0-9]+).png", TileHandler),
    ])


def main():
    app = make_app()
    if DEBUG:
        app.listen(8080)
    else:
        server = HTTPServer(app)
        server.bind(8080)
        server.start(0)  # forks one process per cpu

    ioloop.IOLoop.instance().start()
    import tcelery

    tcelery.setup_nonblocking_producer(celery_app=tasks.celery)


if __name__ == "__main__":
    main()
    # application.listen(8080)
    # ioloop.IOLoop.instance().start()
