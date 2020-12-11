# A server which uses mediapipe with a camera (webcam) to detect hands. It draws
# the hands on the screen, and hosts a flask server in another thread to allow 
# getting the most recent hands data over the web. The data is accessible from
# localhost:5000 via get requests, and it is in the JSON format.
#
# Author: Ardalan Ahanchi
# Date: November 2020

# Imports ######################################################################

import threading            # For multi-threading.
import sys                  # For reading terminal arguments.
import json                 # For serializing the landmark class into json.
from json import JSONEncoder# For encoding into json.

# For hand recognition, and image manipulation (reading from webcam, etc.)
import cv2
import mediapipe

# For the web server which makes the information accessible to unity.
from flask import Flask, make_response

# Constants ####################################################################
DEFAULT_CAMERA_ID = 0
DEFAULT_DETECTION_CONFIDECE = 0.75
DEFAULT_TRACKING_CONFIDENCE = 0.5
VIEW_WINDOW_TITLE = "Hand Recognition View"

# Shared variables (between threads) ###########################################
app = Flask(__name__)          # The main Flask instance used by the webserver.
lock = threading.Lock()        # The lock which is used for synchronization.
hands_data = {}                # Holds the most current landmarks.

# Landmark management ##########################################################

# A class which represents a single landmark (important key-point wihtin
# the hand). It is used to allow easy access to the data fields.
class Landmark:    
    # The constructor which creates an empty landmark object.
    def __init__(self):
        pass
        
    # A method which overrides the function variables with the ones passed 
    # from mediapipe_landmark. It is done to improve function visibility.
    def set(self, mediapipe_landmark):
        # Set the coordinates.
        self.x = mediapipe_landmark.x
        self.y = mediapipe_landmark.y
        self.z = mediapipe_landmark.z
        
        # Set the additional attributes.
        self.visibility = mediapipe_landmark.visibility
        self.presence = mediapipe_landmark.presence

    # A function which returns a list of "count" empty Landmarks.
    def new_list(count):
        # Define an empty list.
        created_list = []
        
        # Add empty Landmark object to it.
        for idx in range(count):
            created_list.append(Landmark())
            
        return created_list

# A class which helps in the encoding of landmark objects into JSON.
# It's specification is based on what JSONEncoder documentation provides.
class LandmarkEncoder(JSONEncoder):
        def default(self, lm_object):
            return lm_object.__dict__
            
# A function which turns the hands data with the given label into ("Left" or 
# "Right") a json representation in a response format with the proper code.
# If everything is alright, it returns a 200 code, otherwise a 404.
def get_response(hand_label):
    # Grab the lock since we'll be reading from hands_data.
    lock.acquire()
    
    # If the hands_data is not populated for the required label, return 
    # a 404 not found return status.
    if hand_label not in hands_data:
        response = make_response("Error: Could not find label", 404)
    else:  
        # Otherwise, grab the Json with the given specific encoder.
        response = make_response(json.dumps(hands_data[hand_label], \
            cls=LandmarkEncoder), 200)
    
    # Release the lock since we're done reading from hands_data.
    lock.release()
    
    # return the json representation.
    return response

# Web server code ##############################################################

# A function (view) which is called when there is a get request to 
# localhost:port/hands/left URL. 
# It returns a JSON object of all the left hand data.
@app.route("/hands/left")
def get_left_hand():
    # Create a response by turning hands_data["Left"] into JSON.
    return get_response("Left")
    
# A function (view) which is called when there is a get request to 
# localhost:port/hands/right URL. 
# It returns a JSON object of all the right hand data.
@app.route("/hands/right")
def get_right_hand():
    # Create a response by turning hands_data["Right"] into JSON.
    return get_response("Right")

# A function which starts the web server when spawned (in a new thread).
def start_webserver():
	app.run()

# Hand detection code ##########################################################

# A function which reads data from the webcam, and runs hand recognition.
# This is partially (the detection code) based on the example provided by
# MediaPipe source code under Apache license 2.0.
# Link: https://google.github.io/mediapipe/solutions/hands.html#python
def start_detection(camera_id, detection_confidence, tracking_confidence):
    # Get the solutions for drawing and hand recognition.
    mp_drawing = mediapipe.solutions.drawing_utils
    mp_hands = mediapipe.solutions.hands

    # Initialize the hand recognition model.
    hands = mp_hands.Hands(min_detection_confidence=detection_confidence, \
        min_tracking_confidence=tracking_confidence)
    
    # Setup the capture device by the camera_id.
    capture = cv2.VideoCapture(camera_id)

    # Continue recieving an image while the webcam is active.
    while capture.isOpened():
        success, image = capture.read()
  
        # Don't continue if we couldn't read from camera.
        if not success:
            break

        # Convert the image color and save it
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # To improve performance, mark the image as not writeable to pass by ref.
        image.flags.writeable = False
        results = hands.process(image)

        # Draw the hand annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Check to see if we got any results from the hands model.
        if results.multi_hand_landmarks:
            # Go through every classified result's information (index, label).
            for idx in range(len(results.multi_hand_landmarks)):                
                # Get the label of this entry ("Left", "Right") for using in dict.
                label = results.multi_handedness[idx].classification[0].label
                
                # Get the hand landmarks based on the index of the classification
                landmarks = results.multi_hand_landmarks[idx]
                
                # Draw the hand on the screen with it's connection.
                mp_drawing.draw_landmarks(image, landmarks, \
                    mp_hands.HAND_CONNECTIONS)

                # Store the list of the landmarks.
                landmarks_list = landmarks.ListFields()[0][1]
                
                # Grab the lock since we'll be writing to the hands_data.
                lock.acquire()
                
                # If the label does not exist in hand data, intialize it.
                # In this case, we create an empty array of 21 which is
                # the size of landmarks.
                if label not in hands_data:
                    hands_data[label] = Landmark.new_list(len(landmarks_list))
                
                # Store the list of data to avoid extra lookups.
                hand_data = hands_data[label]
                
                # Go through the list.
                for landmark_idx in range(len(landmarks_list)):
                    # Set the data in the hand, to the one recieved from algorithm.
                    hand_data[landmark_idx].set(landmarks_list[landmark_idx])
                    
                # Release the lock since we're done writing to hands_data.
                lock.release()
        
        # Display image in the given window, and flip it to get a better window.
        cv2.imshow(VIEW_WINDOW_TITLE, cv2.flip(image, 1))
        
        #cv2.imshow(VIEW_WINDOW_TITLE, image)
        if cv2.waitKey(5) & 0xFF == 27:
            break
    
    # Clean up.
    hands.close()
    capture.release()
    
# Input handling, and initialization code ######################################

# The main function which starts the image detection and the web-server in new
# threads, and waits for them to join back.
def main():
    # Store the camera ID
    cam_id = DEFAULT_CAMERA_ID
    
    # If we have a paramter passed, modify the camera id.
    if len(sys.argv) == 2:
        # If the user requested the help message, display it.
        if sys.argv[1] == "-h" or sys.argv[1] == "--help":
            print("A program which detects hand coordinates using mediapipe.")
            print("and hosts them on a web-server.\n")
            print("Author: Ardalan Ahanchi")
            print("Date: November 2020\n")
            print("To use: python3 server.py")
            print("        python3 server.py [camera_id]")
        else:
            # Try to convert the camera ID to an integer and set it.
            try:  
                cam_id = int(sys.argv[1])
            except:
                cam_id = DEFAULT_CAMERA_ID
                print("Invalid camera ID passed. Using default.")
    
    # Print the initialization message.
    print("Starting the server for camera", cam_id)
    
    # Initialize the threads.
    detection_thread = threading.Thread(target=start_detection, 
        args=(cam_id, DEFAULT_DETECTION_CONFIDECE, DEFAULT_TRACKING_CONFIDENCE))
    
    webserver_thread = threading.Thread(target=start_webserver)
    
    # Start the threads.
    detection_thread.start()
    webserver_thread.start()
    
    # Wait for the threads to come back.
    detection_thread.join()
    webserver_thread.join()
    
# Run the main function if necessary.
if __name__ == "__main__":
    main()

