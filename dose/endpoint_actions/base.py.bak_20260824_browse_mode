from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class EndpointAction:
    key: str
    kind: str
    title: str
    publish: Callable
    build_payload: Callable


class EndpointActionAdapter:
    surface_template = ""
    default_bookmarks = ()

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        return False

    def actions(self) -> dict[str, EndpointAction]:
        return {}

    def action(self, key: str) -> EndpointAction | None:
        return self.actions().get((key or "").strip().lower())
