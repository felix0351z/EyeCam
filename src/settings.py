import os


class EyeCamSettings:
    PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
    COCO_FILE_PATH = PROJECT_PATH + "/models/coco.names"

    # How many frames are between a fps measurement
    FPS_AVG_MEASURE_TIME = 10
    # Threshold
    SCORE_THRESHOLD = 0.5
    NMS_THRESHOLD = 0.45
