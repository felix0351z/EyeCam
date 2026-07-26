import os
from ultralytics import YOLO

name_yolo26 = "yolo26n"
name_yolo8  = "yolov8n"
name_yolo5  = "yolov5n"

# Build and export the model to the onnx format
model = YOLO(model=f"{name_yolo26}.pt")

# Accepted formats: onnx, openvino, ...
model.export(format="onnx", end2end=True)
