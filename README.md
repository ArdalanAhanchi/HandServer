# HandServer

A RESTful server which can get hand recognition data from mediapipe and host it for the clients to use.



* *Author* : Ardalan Ahanchi
* *Date* : December 2020

## Dependencies
To run the server, you'll have to install python (tested with version 3.8.6) and it's package manager.
then you'll have to install the following dependencies.
* Mediapipe `pip install mediapipe`
* Flask `pip install Flask`

## To run
Run the server program. Optionally, you can pass the camera ID as the first argument.
* *Camera ID 0* : `python server.py`
* *Camera ID 2* : `python server.py 2`

## Endpoints
* *Left hand* : http://localhost:5000/hands/left 
* *Right hand* : http://localhost:5000/hands/right 
