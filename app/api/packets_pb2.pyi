from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
SENSOR_LEFT: GraphLabel
SENSOR_MIDDLE: GraphLabel
SENSOR_RIGHT: GraphLabel
YOLO_LEFT: GraphLabel
YOLO_MIDDLE: GraphLabel
YOLO_RIGHT: GraphLabel

class Command(_message.Message):
    __slots__ = ["running"]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    running: bool
    def __init__(self, running: bool = ...) -> None: ...

class GraphPacket(_message.Message):
    __slots__ = ["frame_id", "graphs"]
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    GRAPHS_FIELD_NUMBER: _ClassVar[int]
    frame_id: int
    graphs: _containers.RepeatedCompositeFieldContainer[GraphValue]
    def __init__(self, frame_id: _Optional[int] = ..., graphs: _Optional[_Iterable[_Union[GraphValue, _Mapping]]] = ...) -> None: ...

class GraphValue(_message.Message):
    __slots__ = ["name", "value"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    name: GraphLabel
    value: float
    def __init__(self, name: _Optional[_Union[GraphLabel, str]] = ..., value: _Optional[float] = ...) -> None: ...

class Packet(_message.Message):
    __slots__ = ["graph", "sensor", "status", "yolo"]
    GRAPH_FIELD_NUMBER: _ClassVar[int]
    SENSOR_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    YOLO_FIELD_NUMBER: _ClassVar[int]
    graph: GraphPacket
    sensor: SensorPacket
    status: StatusPacket
    yolo: YoloPacket
    def __init__(self, yolo: _Optional[_Union[YoloPacket, _Mapping]] = ..., sensor: _Optional[_Union[SensorPacket, _Mapping]] = ..., graph: _Optional[_Union[GraphPacket, _Mapping]] = ..., status: _Optional[_Union[StatusPacket, _Mapping]] = ...) -> None: ...

class SensorPacket(_message.Message):
    __slots__ = ["distance_mm", "range_sigma_mm", "target_status"]
    DISTANCE_MM_FIELD_NUMBER: _ClassVar[int]
    RANGE_SIGMA_MM_FIELD_NUMBER: _ClassVar[int]
    TARGET_STATUS_FIELD_NUMBER: _ClassVar[int]
    distance_mm: bytes
    range_sigma_mm: bytes
    target_status: bytes
    def __init__(self, distance_mm: _Optional[bytes] = ..., target_status: _Optional[bytes] = ..., range_sigma_mm: _Optional[bytes] = ...) -> None: ...

class StatusPacket(_message.Message):
    __slots__ = ["running"]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    running: bool
    def __init__(self, running: bool = ...) -> None: ...

class YoloPacket(_message.Message):
    __slots__ = ["boxes", "class_ids", "confidences", "frame_id", "jpeg_bytes", "timestamp_ms"]
    BOXES_FIELD_NUMBER: _ClassVar[int]
    CLASS_IDS_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCES_FIELD_NUMBER: _ClassVar[int]
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    JPEG_BYTES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    boxes: bytes
    class_ids: bytes
    confidences: bytes
    frame_id: int
    jpeg_bytes: bytes
    timestamp_ms: int
    def __init__(self, frame_id: _Optional[int] = ..., timestamp_ms: _Optional[int] = ..., jpeg_bytes: _Optional[bytes] = ..., confidences: _Optional[bytes] = ..., class_ids: _Optional[bytes] = ..., boxes: _Optional[bytes] = ...) -> None: ...

class GraphLabel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
