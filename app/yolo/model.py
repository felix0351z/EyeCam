import abc
import numpy as np
import ncnn
from yolo.classes import YOLOInput, LetterboxTransform, YOLOOutput
from yolo.utils import letterbox, resize_boxes_central_coordinates, nms

THRESHOLD = 0.2

def pre_process(image: np.ndarray) -> YOLOInput:
    resized, transform = letterbox(image)
    height, width = resized.shape[:2]

    # Convert it in to a Mat object and switch BGR to RGB
    mat_in = ncnn.Mat.from_pixels(
        resized,
        ncnn.Mat.PixelType.PIXEL_BGR2RGB,
        width, height
    )

    # Perform a normalization
    mean_vals = [0.0, 0.0, 0.0]
    norm_vals = [1 / 255.0, 1 / 255.0, 1 / 255.0]
    mat_in.substract_mean_normalize(mean_vals, norm_vals)

    return YOLOInput(mat_in, transform)



class YoloModel(abc.ABC):
    """
    NCNN is a framework specialized for embedded devices by Tencent.
    This is usually one of the best frameworks to run with a Raspberry Pi
    """

    def __init__(self, model_folder: str):
        self.net = ncnn.Net()
        self.net.load_param(model_folder + "/model.ncnn.param")
        self.net.load_model(model_folder + "/model.ncnn.bin")

    def infer(self, data: YOLOInput) -> np.ndarray:
        extractor = self.net.create_extractor()
        extractor.input("in0", data.input)

        ret, out = extractor.extract("out0")
        return np.expand_dims(np.array(out), axis=0)

    @abc.abstractmethod
    def post_process(self, image: np.ndarray, net: np.ndarray, transform: LetterboxTransform) -> YOLOOutput:
        pass


class YoloV5(YoloModel):

    def __init__(self, model_folder: str):
        super().__init__(model_folder)

    def post_process(self, image: np.ndarray, net: np.ndarray, transform: LetterboxTransform) -> YOLOOutput:
        # YOLOv5 model output has shape (1, n ,85)
        # [center x, center y, width, height, objectness and 80 coco class scores]

        scores = net[0, :, 5:]
        confidences = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)

        mask = confidences > THRESHOLD

        boxes = net[0, mask, :4]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        # Resize the boxes and change format to [left, top, width, height]
        boxes = resize_boxes_central_coordinates(boxes, transform)
        output = YOLOOutput(image, confidences, class_ids, boxes)

        # Apply NMS
        nms(data=output, score_threshold=THRESHOLD)
        return output



class YoloV26(YoloModel):

    def __init__(self, model_folder: str):
        super().__init__(model_folder)

    def post_process(self, image: np.ndarray, net: np.ndarray, transform: LetterboxTransform) -> YOLOOutput:
        # [center x, center y, width, height, and 80 coco class scores]
        # YOLOv8 has twisted axes
        detections = np.transpose(net[0])

        # Get confidences and class ids from the detections
        scores = detections[:, 4:]
        confidences = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)

        # Only take values over threshold
        mask = confidences > THRESHOLD

        boxes = detections[mask, :4]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        # Resize the boxes and change format to [left, top, width, height]
        boxes = resize_boxes_central_coordinates(boxes, transform)
        output = YOLOOutput(image, confidences, class_ids, boxes)

        # Apply NMS
        nms(data=output, score_threshold=THRESHOLD)
        return output