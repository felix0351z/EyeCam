## Structure
Idea for the architecture of the app

```bash
yolo/           
  classes.py    # Data-Classes for YOLO-Model, data classes etc. 
  model.py      # The implemented YOLO models with NCNN
  utils.py      # Utility functions for resizing, nms, etc.
sensor/
  ...           # All python files for the vl53l5cx
detection/    
  ...           # All files for the general obstacle detection algorithms
sender.py       # TCP/UDP-Connection between this app and the Preview App
main.py         # Camera capture and main processing pipeline
```