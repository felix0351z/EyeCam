import numpy as np

from yolo.interfaces import Framework, YOLOInput
from yolo.utils.letterbox import letterbox

import ncnn


class NCNNFramework(Framework):
    """
    NCNN is a framework specialized for embedded devices by Tencent.
    This is usually one of the best frameworks to run with a Raspberry Pi
    """

    def __init__(self, config: dict):
        self.net = ncnn.Net()
        self.net.load_param(config["model_path"] + "/model.ncnn.param")
        self.net.load_model(config["model_path"] + "/model.ncnn.bin")

    def pre_process(self, image: np.ndarray) -> YOLOInput:
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



    def infer(self, data: YOLOInput) -> np.ndarray:
        extractor = self.net.create_extractor()
        extractor.input("in0", data.input)

        ret, out = extractor.extract("out0")
        return np.expand_dims(np.array(out), axis=0)