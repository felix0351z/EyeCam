# YOLO-Model export with ultralytics 

```bash
# 1. Create a new conda environment for the builder
conda create --name eyecam-builder

# 2. Activate the new environment
conda deactivate && conda activate eyecam-builder

# 2. Install dependencies
conda install conda-forge::ultralytics conda-forge::torchvision

# 3. Export models with builder.py
python builder.py <yolo-model-name> <format>
python builder.py yolo26n ncnn

```
