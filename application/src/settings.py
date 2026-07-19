import os


class EyeCamSettings:
    PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
    """
    The root project path.
    This is the src/ folder here
    """

    COCO_FILE_PATH = PROJECT_PATH + "/models/coco.names"
    """
    Path to the coco.names file.
    """

    FPS_AVG_MEASURE_TIME = 10
    """
    How many frames are between a fps measurement
    """

    SCORE_THRESHOLD = 0.5
    """
    If the confidence of a detection is over the threshold, it will be considered valid.
    if not, it will be discarded.
    """

    NMS_THRESHOLD = 0.45
    """
    Use this as overlapping threshold if a Non-Maximum-Suppression (NMS) is needed
    """
