"""Public session bridge disabled — commercial-track / private."""

from __future__ import annotations


class PortalSession:
    """Stub. Proprietary session/trajectory wiring is private."""

    def __init__(self, *args, **kwargs) -> None:
        raise RuntimeError(
            "PortalSession is commercial-track / private on public GitHub."
        )


def timed() -> float:
    raise RuntimeError("timed() is commercial-track / private on public GitHub.")
