#Pyler - A python tile server

##Plan:
- [x] Use Tornado instead of flask
- [x] Use Protobuf to create a metatile storage format (store 64 - 8x8 tiles in one file)
- [x] Render tiles as an 8x8 metatile
- [x] Distribute render tasks with Celery
- [x] User Redis as a lock service to prevent the same metatile being rendered multiple times
- [x] Figure out a way to configure/read styles to use
