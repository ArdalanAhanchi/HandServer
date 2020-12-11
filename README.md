# HandServer

A RESTful server which can get hand recognition data from mediapipe and host it for the clients to use.

## Dependencies
* Python3
* Mediapipe `pip3 install mediapipe`
* Flask `pip3 install Flask`

## To run
Run the server program. Optionally, you can pass the camera ID as the first argument.
* Camera ID 0: `python3 server.py`
* Camera ID 2: `python3 server.py 2`

## Endpoints
* Left hand: http://localhost:5000/hands/left 
* Right hand: http://localhost:5000/hands/right 
