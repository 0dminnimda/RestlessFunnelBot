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


def _find_mapper_key(type: Type[T]) -> Optional[Type[Any]]:
    intersection = _model_mappers.keys() & ((type,) + type.__bases__)
    if len(intersection) == 0:
        return None
    elif len(intersection) == 1:
        return intersection.pop()
    else:
        assert False, "Not Implemented yet"


def _sub_map_model(
    obj: Any, extra: Dict[str, Any], recursive: bool
) -> Optional[Dict[str, Any]]:
    key = _find_mapper_key(type(obj))
    if key is None:
        return None
    model, mapper = _model_mappers[key]

    fields = {**extra, **mapper(obj)}
    if recursive:
        for name, value in fields.items():
            sub_result = _sub_map_model(value, extra, recursive)
            if sub_result is not None:
                fields[name] = sub_result

    return fields


def map_model(
    obj: Any,
    extra: Dict[str, Any] = dict(),
    recursive: bool = False,
) -> Dict[str, Any]:
    result = _sub_map_model(obj, extra, recursive)
    if result is None:
        raise KeyError(f"No mapping found for type {type(obj)}")
    return result
