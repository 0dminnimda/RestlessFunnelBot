from time import time
from typing import (
    Any,
    Dict,
    Generic,
    Hashable,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
T = TypeVar("T", bound=Any)


class TTLValue(Generic[V]):
    __slots__ = "value", "expires"

    value: V
    expires: float

    def __init__(self, value: V, ttl: float) -> None:
        self.value = value
        self.expires = time() + ttl

    def __repr__(self) -> str:
        names = ["value", "expires"]
        args = [f"{name}={getattr(self, name)}" for name in names]
        return type(self).__name__ + "(" + ", ".join(args) + ")"


_Val = TTLValue[V]


_DEFAULT: Any = object()


class TTLDict(Dict[K, V]):
    __slots__ = "_ttl", "expire_count"

    _ttl: float
    expire_count: int

    def __init__(self, ttl: float, expire_count: int = -1) -> None:
        self._ttl = ttl
        self.expire_count = expire_count

    # def __contains__(self, key: Any) -> bool:
    #     # self.expire()
    #     return super().__contains__(key)

    def __getitem__(self, key: K) -> V:
        # self.expire()
        value = cast(_Val, super().__getitem__(key))
        if time() <= value.expires:
            return value.value
        super().__delitem__(key)
        return cast(_Val, super().__getitem__(key)).value

    def __setitem__(self, key: K, value: V) -> None:
        # self.expire()
        if not isinstance(value, TTLValue):
            value = cast(V, TTLValue(value, self._ttl))
        super().__setitem__(key, value)

    # def __delitem__(self, key: K) -> None:
    #     # self.expire()
    #     super().__delitem__(key)

    # I don't need this right now
    # def __iter__(self) -> Iterator[K]:
    #     for key, value in self.items():
    #         yield key

    # I don't need this right now
    # def items(self) -> Iterable[Tuple[K, V]]:  # type: ignore[override]
    #     current_time = time()
    #     for key, value in cast(Iterable[Tuple[K, _Val]], super().items()):
    #         if current_time <= value.expires:
    #             yield key, value.value

    def get(self, key: K, default: Optional[Union[V, T]] = None) -> Union[V, T]:
        value_ = super().get(key, default)  # type: ignore
        if value_ is default:
            return value_
        value = cast(_Val, value_)
        if time() <= value.expires:
            return value.value
        super().__delitem__(key)
        return cast(Union[V, T], default)

    def pop(self, key: K, default: Union[V, T] = _DEFAULT) -> Union[V, T]:
        if default is _DEFAULT:
            result = super().pop(key)
        else:
            result = super().pop(key, default)
            if result is default:
                return default
        return cast(_Val, result).value

    def expire(self) -> List[V]:
        """
        Removes and returns expired items from the dict.
        ---
        This function relies on the fact that dict is ordered.
        More often calls -> faster execution time.
        Complexity is ~O(n*sigmiod(x)) where n is number of keys
        and x is how much time passed from the last update.
        """

        keys = []
        count = self.expire_count

        current_time = time()
        for key, value in super().items():
            if current_time <= cast(_Val, value).expires:
                break
            keys.append(key)

            count -= 1
            if count == 0:
                break

        return [self.pop(key) for key in keys]
