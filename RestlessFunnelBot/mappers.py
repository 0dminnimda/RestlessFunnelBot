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
    obj: T, extra: Dict[str, Any], handler: Callable[[Any], Any], recursive: bool
) -> Optional[M]:
    key = _find_mapper_key(type(obj))
    if key is None:
        return None
    model, mapper = _model_mappers[key]

    fields = {**extra, **mapper(obj)}
    if recursive:
        for name, value in fields.items():
            sub_result = _sub_map_model(value, extra, handler, recursive)
            if sub_result is not None:
                fields[name] = sub_result

    result = model(**fields)
    handler(result)
    return result


def map_model(
    obj: Any,
    extra: Dict[str, Any],
    handler: Callable[[Any], Any] = lambda x: x,
    recursive: bool = False,
) -> Any:
    result = _sub_map_model(obj, extra, handler, recursive)
    if result is None:
        raise KeyError(f"No mapping found for type {type(obj)}")
    return result


# def _sub_map_model(fields: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
#     for key, obj in fields.items():
#         result = _find_mapper_key(type(obj))
#         if result is not None:
#             model, mapper = _model_mappers[result]
#             new_fields = _sub_map_model(mapper(obj), extra)
#             fields[key] = model(**new_fields, **extra)
#     return fields


# def map_model(obj: T, extra: Dict[str, Any], recursive: bool = False) -> M:
#     result = _find_mapper_key(type(obj))
#     if result is None:
#         raise KeyError(f"No mapping found for type {type(obj)}")
#     model, mapper = _model_mappers[result]

#     fields = mapper(obj)
#     if recursive:
#         fields = _sub_map_model(fields, extra)
#     return model(**fields, **extra)
