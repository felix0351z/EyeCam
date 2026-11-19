import sys
from ultralytics import YOLO

if len(sys.argv) != 3:
    print("Please provide a valid yolo model name and an export format.\n"
          "Use python builder.py <yolo-model-name> <export-format>")
    exit(1)

# Load the model from the .pt file.
# If the file isn't available it will be downloaded.
# Then export the model.
# See https://docs.ultralytics.com/modes/export#arguments
model = YOLO(model=f"{sys.argv[1]}.pt")
model.export(format=sys.argv[2], imgsz=320)
