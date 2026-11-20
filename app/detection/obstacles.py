"""
Central list of all COCO classes, which count as obstacles for the detection algorithms.
Used by all algorithms with a camera part (sensor_first, parcours, parcours_stable).

The key is the COCO class id, which equals the line number (starting at 0)
in analyzer/assets/coco.names.

After changing this list, update the class names for the Analyzer with:
    python -m detection.obstacles
"""

OBSTACLE_CLASSES: dict[int, str] = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    10: "fire hydrant",
    11: "stop sign",
    12: "parking meter",
    13: "bench",
    15: "cat",
    16: "dog",
    24: "backpack",
    25: "umbrella",
    28: "suitcase",
    41: "cup",
    56: "chair",
    57: "couch",
    58: "potted plant",
    59: "bed",
    60: "dining table",
    61: "toilet",
}


def write_names_file(coco_path: str, out_path: str):
    """
    Writes a copy of coco.names, which only contains the obstacle classes.
    All other lines stay empty, so the line number still equals the class id.
    """
    with open(coco_path) as f:
        coco_names = f.read().splitlines()

    for class_id, name in OBSTACLE_CLASSES.items():
        if coco_names[class_id] != name:
            raise ValueError(f"Class {class_id} is '{coco_names[class_id]}' in coco.names, not '{name}'")

    lines = [name if i in OBSTACLE_CLASSES else "" for i, name in enumerate(coco_names)]
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    from pathlib import Path

    assets = Path(__file__).resolve().parents[2] / "analyzer" / "assets"
    write_names_file(str(assets / "coco.names"), str(assets / "obstacles.names"))
    print(f"Written {assets / 'obstacles.names'} ({len(OBSTACLE_CLASSES)} classes)")
