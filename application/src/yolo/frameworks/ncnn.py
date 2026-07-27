import numpy as np

from yolo.interfaces import Framework, YOLOInput
from yolo.utils.letterbox import letterbox


class NCNNFramework(Framework):
    """
    NCNN is a framework specialized for embedded devices by Tencent.
    This is usually one of the best frameworks to run with a Raspberry Pi
    """

    def __init__(self, config: dict):
        self.ncnn = __import__("ncnn")

        self.net = self.ncnn.Net()
        self.net.load_param(config["model_path"] + "/model.ncnn.params")
        self.net.load_model(config["model_path"] + "/model.ncnn.bin")
        self.extractor = self.net.create_extractor()

    def pre_process(self, image: np.ndarray) -> YOLOInput:
        resized, transform = letterbox(image)
        height, width = resized.shape[:2]

        # Convert it in to a Mat object and switch BGR to RGB
        mat = self.ncnn.Mat.from_pixels(
            resized,
            self.ncnn.Mat.PixelType.PIXEL_BGR2RGB,
            width, height
        )

        return YOLOInput(mat, transform)



    def infer(self, data: YOLOInput) -> np.ndarray:
        self.extractor.input("in0", data.input)

        ret, out = self.extractor.extract("out0")
        return np.expand_dims(np.array(out), axis=0)