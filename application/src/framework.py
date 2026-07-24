import abc
import numpy as np

from importlib.util import find_spec


class Framework(abc.ABC):

    @abc.abstractmethod
    def __init__(self, model_path: str):
        """
        The path to the model file
        Take a look at the various frameworks to see what it should point to.

        The model_path is set in the settings.py file
        """
        pass

    @abc.abstractmethod
    def forward(self, input_frame: np.ndarray) -> np.ndarray:
        """
        Feed the model with new data and take the result from the output layer.
        """
        pass


def load(model_path: str) -> Framework:
    """
    Load the correct framework depending on the installed libraries.
    """

    if find_spec("ncnn") is not None:
        print("Loading NCNN framework")
        return NCNNFramework(model_path)
    elif find_spec("openvino") is not None:
        print("Loading OpenVINO framework")
        return OpenVinoFramework(model_path)
    else:
        print("Loading OpenCV ONNX framework")
        return OpenCVOnnxFramework(model_path)


class OpenCVOnnxFramework(Framework):
    """
    Use the Deep-Neural-Network Module (dnn) from OpenCV.
    This supports the ONNX engine to run .onnx models.

    The model path should point to the .onnx file
    """

    def __init__(self, model_path: str):
        cv = __import__("cv2")
        self.net: cv.dnn.Net = cv.dnn.readNet(model_path)

    def forward(self, input_frame: np.ndarray) -> np.ndarray:
        print("forward onnx")
        self.net.setInput(input_frame)
        return self.net.forward(self.net.getUnconnectedOutLayersNames())[0]


class OpenVinoFramework(Framework):
    """
    OpenVINO is a framework by Intel to run AI models on Intel CPUs and embedded platforms.
    The model has two files: the .xml and .bin

    The model_path should point to the .xml file. OpenVINO automatically searches for the .bin file in the same directory.
    """

    def __init__(self, model_path: str):
        ov = __import__("openvino")
        core = ov.Core()
        model = core.read_model(model_path)

        self.ov_compiled_model = core.compile_model(model, device_name="AUTO")
        self.ov_output_layer = self.ov_compiled_model.output(0)

    def forward(self, input_frame: np.ndarray) -> np.ndarray:
        print("forward openvino")
        return self.ov_compiled_model(inputs=[input_frame])[self.ov_output_layer]


class NCNNFramework(Framework):
    """
    NCNN is a framework specialized for embedded devices by Tencent.
    This is usually one of the best frameworks to run with a Raspberry Pi

    The model path should point to the files, where the .bin and .param files are in.
    """

    def __init__(self, model_dir_path: str):
        self.ncnn = __import__("ncnn")

        self.net = self.ncnn.Net()
        self.net.load_param(f"{model_dir_path}/model.ncnn.param")
        self.net.load_model(f"{model_dir_path}/model.ncnn.bin")
        self.extractor = self.net.create_extractor()

    def forward(self, input_frame: np.ndarray) -> np.ndarray:
        print("forward ncnn")
        mat = self.ncnn.Mat(input_frame)
        self.extractor.input("in0", mat)

        ret, out = self.extractor.extract("out0")
        print(np.array(out).shape)
        return np.array(out)