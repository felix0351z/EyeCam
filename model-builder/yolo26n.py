from ultralytics import YOLO

model = YOLO(model="yolov8n.pt")
model.export(format="onnx")

print(model.names)