from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GraphLabel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ZONE_LEFT: _ClassVar[GraphLabel]
    ZONE_MIDDLE: _ClassVar[GraphLabel]
    ZONE_RIGHT: _ClassVar[GraphLabel]
ZONE_LEFT: GraphLabel
ZONE_MIDDLE: GraphLabel
ZONE_RIGHT: GraphLabel

class YoloPacket(_message.Message):
    __slots__ = ("frame_id", "timestamp_ms", "jpeg_bytes", "confidences", "class_ids", "boxes")
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    JPEG_BYTES_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCES_FIELD_NUMBER: _ClassVar[int]
    CLASS_IDS_FIELD_NUMBER: _ClassVar[int]
    BOXES_FIELD_NUMBER: _ClassVar[int]
    frame_id: int
    timestamp_ms: int
    jpeg_bytes: bytes
    confidences: bytes
    class_ids: bytes
    boxes: bytes
    def __init__(self, frame_id: _Optional[int] = ..., timestamp_ms: _Optional[int] = ..., jpeg_bytes: _Optional[bytes] = ..., confidences: _Optional[bytes] = ..., class_ids: _Optional[bytes] = ..., boxes: _Optional[bytes] = ...) -> None: ...

class GraphValue(_message.Message):
    __slots__ = ("name", "value")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    name: GraphLabel
    value: float
    def __init__(self, name: _Optional[_Union[GraphLabel, str]] = ..., value: _Optional[float] = ...) -> None: ...

class GraphPacket(_message.Message):
    __slots__ = ("frame_id", "graphs")
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    GRAPHS_FIELD_NUMBER: _ClassVar[int]
    frame_id: int
    graphs: _containers.RepeatedCompositeFieldContainer[GraphValue]
    def __init__(self, frame_id: _Optional[int] = ..., graphs: _Optional[_Iterable[_Union[GraphValue, _Mapping]]] = ...) -> None: ...

class Packet(_message.Message):
    __slots__ = ("yolo", "graph")
    YOLO_FIELD_NUMBER: _ClassVar[int]
    GRAPH_FIELD_NUMBER: _ClassVar[int]
    yolo: YoloPacket
    graph: GraphPacket
    def __init__(self, yolo: _Optional[_Union[YoloPacket, _Mapping]] = ..., graph: _Optional[_Union[GraphPacket, _Mapping]] = ...) -> None: ...
