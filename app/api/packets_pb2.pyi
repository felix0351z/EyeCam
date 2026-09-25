from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
ZONE_LEFT: GraphLabel
ZONE_MIDDLE: GraphLabel
ZONE_RIGHT: GraphLabel

class Detection(_message.Message):
    __slots__ = ["class_id", "confidence", "x1", "x2", "y1", "y2"]
    CLASS_ID_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    X1_FIELD_NUMBER: _ClassVar[int]
    X2_FIELD_NUMBER: _ClassVar[int]
    Y1_FIELD_NUMBER: _ClassVar[int]
    Y2_FIELD_NUMBER: _ClassVar[int]
    class_id: int
    confidence: float
    x1: float
    x2: float
    y1: float
    y2: float
    def __init__(self, class_id: _Optional[int] = ..., confidence: _Optional[float] = ..., x1: _Optional[float] = ..., y1: _Optional[float] = ..., x2: _Optional[float] = ..., y2: _Optional[float] = ...) -> None: ...

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
    __slots__ = ["graph", "yolo"]
    GRAPH_FIELD_NUMBER: _ClassVar[int]
    YOLO_FIELD_NUMBER: _ClassVar[int]
    graph: GraphPacket
    yolo: YoloPacket
    def __init__(self, yolo: _Optional[_Union[YoloPacket, _Mapping]] = ..., graph: _Optional[_Union[GraphPacket, _Mapping]] = ...) -> None: ...

class YoloPacket(_message.Message):
    __slots__ = ["detections", "frame_id", "jpeg_bytes", "timestamp_ms"]
    DETECTIONS_FIELD_NUMBER: _ClassVar[int]
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    JPEG_BYTES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    detections: _containers.RepeatedCompositeFieldContainer[Detection]
    frame_id: int
    jpeg_bytes: bytes
    timestamp_ms: int
    def __init__(self, frame_id: _Optional[int] = ..., timestamp_ms: _Optional[int] = ..., jpeg_bytes: _Optional[bytes] = ..., detections: _Optional[_Iterable[_Union[Detection, _Mapping]]] = ...) -> None: ...

class GraphLabel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
