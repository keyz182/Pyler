#Pyler - A python tile server

##Plan:
- [x] Use Tornado instead of flask
- [x] Use Protobuf to create a metatile storage format (store 64 - 8x8 tiles in one file)
- [x] Render tiles as an 8x8 metatile
- [x] Distribute render tasks with Celery
- [x] User Redis as a lock service to prevent the same metatile being rendered multiple times
- [x] Figure out a way to configure/read styles to use

##Installing
You'll need mapnik2 installed, along with python bindings. Currently only tested with python 2.7, if I can get the mapnik bindings for python 3 installed, I'll test with those.
You'll also need redis

###For Ubuntu 14.04:
```
sudo add-apt-repository ppa:mapnik/v2.2.0
sudo apt-get update
sudo apt-get install libmapnik libmapnik-dev mapnik-utils python-mapnik
```


To install redis
```
sudo apt-get install redis-server
```

You also need the requirements specified in requirements.txt. ```pip``` is the easiest way to install these.

```pip install -r requirements.txt```

###Map Styles
In config.py, edit the MAPS list. Add a tuple with the mapname, and the path to the mapnik style xml.

To convert a CartoCSS style to mapnik xml, use the ```carto``` command from [Mapnik](https://github.com/mapbox/carto).

##Running

```$ python pyler.py```

```$ celery -A tasks.celery worker --loglevel=INFO --concurrency=3```