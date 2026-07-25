import sys
from ultralytics import YOLO

if sys.argv[1] is None:
    print("Please provide a valid yolo model name\n"
          "Use python builder.py <yolo-model-name <export-format>")
    exit(1)

if sys.argv[2] is None:
    print("Please provide a export format.\n"
          "Use python builder.py <yolo-model-name <export-format>")
    exit(1)

# Load the model from the .pt file.
# If the file isn't available it will be downloaded.
# Then export the model.
# See https://docs.ultralytics.com/modes/export#arguments
model = YOLO(model=f"{sys.argv[1]}.pt")
model.export(format=sys.argv[2])
