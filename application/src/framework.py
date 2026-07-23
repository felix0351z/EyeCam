import abc
import numpy as np

from importlib.util import find_spec


class Framework(abc.ABC):

    @abc.abstractmethod
    def __init__(self, model_path: str):
        pass

    @abc.abstractmethod
    def forward(self, input_frame: np.ndarray) -> np.ndarray:
        pass


def load(model_path: str) -> Framework:
    if find_spec("ncnn") is not None:
        return NCNNFramework(model_path)
    elif find_spec("openvino") is not None:
        return OpenVinoFramework(model_path)
    else:
        return OpenCVOnnxFramework(model_path)


class OpenCVOnnxFramework(Framework):

    def __init__(self, model_path: str):
        cv = __import__("cv2")
        self.net: cv.dnn.Net = cv.dnn.readNet(model_path)

    def forward(self, input_frame: np.ndarray) -> np.ndarray:
        self.net.setInput(input_frame)
        return self.net.forward(self.net.getUnconnectedOutLayersNames())[0]


class OpenVinoFramework(Framework):

    def __init__(self, model_path: str):
        ov = __import__("openvino")
        core = ov.Core()
        model = core.read_model(model_path)

        self.ov_compiled_model = core.compile_model(model, device_name="AUTO")
        self.ov_output_layer = self.ov_compiled_model.output(0)

    def forward(self, input_frame: np.ndarray) -> np.ndarray:
        return self.ov_compiled_model(inputs=[input_frame])[self.ov_output_layer]


class NCNNFramework(Framework):

    def __init__(self, model_dir_path: str):
        self.ncnn = __import__("ncnn")

        self.net = self.ncnn.Net()
        self.net.load_param(f"{model_dir_path}/.param")
        self.net.load_model(f"{model_dir_path}/.bin")
        self.extractor = self.net.create_extractor()

    def forward(self, input_frame: np.ndarray) -> np.ndarray:
        mat = self.ncnn.Mat(input_frame)
        self.extractor.input("in0", mat)

        ret, out = self.extractor.extrat("out0")
        return np.array(out)