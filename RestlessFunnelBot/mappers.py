from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar

T = TypeVar("T", bound=Any)
M = TypeVar("M", bound=Any)
Mapper = Callable[[T], M]
MapToModel = Dict[Type[T], Tuple[M, Mapper]]


_model_mappers: MapToModel = {}


def model_mapper(type: Type[T], to_type: Type[M]) -> Callable[[Mapper], Mapper]:
    def inner(f: Mapper) -> Mapper:
        _model_mappers[type] = (to_type, f)
        return f

    return inner


def get_mapped_type(type: Type[Any]) -> Optional[Type[Any]]:
    intersection = _model_mappers.keys() & ((type,) + type.__bases__)
    if len(intersection) == 0:
        return None
    elif len(intersection) == 1:
        return intersection.pop()
    else:
        assert False, "Not Implemented yet"


def optional_map_model(obj: Any, recursive: bool) -> Optional[Dict[str, Any]]:
    type_key = get_mapped_type(type(obj))
    if type_key is None:
        return None
    model, mapper = _model_mappers[type_key]

    fields = mapper(obj)
    if not recursive:
        return fields

    for name, value in fields.items():
        sub_result = optional_map_model(value, recursive)
        if sub_result is not None:
            fields[name] = sub_result
    return fields


def map_model(obj: Any, recursive: bool = False) -> Dict[str, Any]:
    result = optional_map_model(obj, recursive)
    if result is None:
        raise KeyError(f"No mapping found for type {type(obj)}")
    return result
