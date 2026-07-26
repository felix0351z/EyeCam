from typing import Type

import numpy as np

from utils.registry import Registry
from yolo.interfaces import Framework, YOLOProcessor, YOLOOutput

from yolo.frameworks.opencv_onnx import OpenCVOnnxFramework
from yolo.frameworks.openvino import OpenvinoFramework
from yolo.frameworks.ncnn import NCNNFramework

from yolo.processors import YOLOv5Processor, YOLOv8Processor, YOLOv26EndToEndProcessor

class YOLOPipeline:

    def __init__(self, framework: Framework, processor: YOLOProcessor):
        self.framework = framework
        self.processor = processor

    def process(self, image: np.ndarray) -> YOLOOutput:
        net_input = self.framework.pre_process(image)
        net_output = self.framework.infer(net_input)
        return self.processor.post_process(image, net_input.transform, net_output)


class YOLO:

    def __init__(self):
        self.framework_registry = Registry[str, Type[Framework]]()
        self.processor_registry = Registry[str, Type[YOLOProcessor]]()

        self._register_frameworks()
        self._register_processors()

    def _register_frameworks(self):
        self.framework_registry.register("onnx", OpenCVOnnxFramework)
        self.framework_registry.register("openvino", OpenvinoFramework)
        self.framework_registry.register("ncnn", NCNNFramework)

    def _register_processors(self):
        self.processor_registry.register("v5", YOLOv5Processor)
        self.processor_registry.register("v8", YOLOv8Processor)
        self.processor_registry.register("v26-end2end", YOLOv26EndToEndProcessor)

    def build_pipeline(self, config: dict) -> YOLOPipeline:
        fw_config = config["yolo"]["framework"]
        p_config = config["yolo"]["processor"]

        fw = self.framework_registry.create(fw_config["name"], fw_config)
        p = self.processor_registry.create(p_config["name"], p_config)
        return YOLOPipeline(fw, p)
