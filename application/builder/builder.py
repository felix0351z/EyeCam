import os
from ultralytics import YOLO

name = "yolo26n"

# Build and export the model to the onnx format
model = YOLO(model=f"{name}.pt")
model.export(format="onnx")

# Place the file in the modules dictionary
os.replace(f"{name}.onnx", f"../src/models/{name}.onnx")