import openvino as ov
import numpy as np

from core.interfaces import Framework, YOLOInput
from processing.blob import create_blob
from processing.letterbox import letterbox


class OpenvinoFramework(Framework):
    """
    OpenVINO is a framework by Intel to run AI models on Intel CPUs and embedded platforms.
    """

    def __init__(self, **kwargs):
        core = ov.Core()
        model = core.read_model(model=kwargs["xml_file"], weights=kwargs["bin_file"])

        self.ov_compiled_model = core.compile_model(model, device_name="AUTO")
        self.ov_output_layer = self.ov_compiled_model.output(0)


    def pre_process(self, image: np.ndarray) -> YOLOInput:
        # Resize the image, create letterbox and transform it to a blob
        resized, transform = letterbox(image)
        blob = create_blob(resized)

        return YOLOInput(blob, transform)

    def infer(self, data: YOLOInput) -> np.ndarray:
        return self.ov_compiled_model(inputs=[data.input])[self.ov_output_layer]
