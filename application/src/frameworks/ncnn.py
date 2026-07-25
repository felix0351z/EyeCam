import ncnn
import numpy as np

from core.interfaces import Framework, YOLOInput
from processing.letterbox import letterbox


class NCNNFramework(Framework):
    """
    NCNN is a framework specialized for embedded devices by Tencent.
    This is usually one of the best frameworks to run with a Raspberry Pi
    """

    def __init__(self, **kwargs):
        self.net = ncnn.Net()
        self.net.load_param(kwargs["param_file"])
        self.net.load_model(kwargs["bin_file"])
        self.extractor = self.net.create_extractor()

    def pre_process(self, image: np.ndarray) -> YOLOInput:
        resized, transform = letterbox(image)
        height, width = resized.shape[:2]

        # Convert it in to a Mat object and switch BGR to RGB
        mat = ncnn.Mat.from_pixels(
            resized,
            ncnn.Mat.PixelType.PIXEL_BGR2RGB,
            width, height
        )

        return YOLOInput(mat, transform)



    def infer(self, data: YOLOInput) -> np.ndarray:
        self.extractor.input("in0", data.input)

        ret, out = self.extractor.extract("out0")
        return np.expand_dims(np.array(out), axis=0)