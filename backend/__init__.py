"""
PatchBounty (@aegis) Backend Package Initializer.
Installs CPython 3.10 - 3.14+ cross-platform (`WindowsProactorEventLoopPolicy` / `BaseDefaultEventLoopPolicy`)
thread-safe asyncio event-loop compatibility guard BEFORE any Fetch.ai `uagents` or `cosmpy` module loads,
eliminating `RuntimeError: There is no current event loop in thread 'MainThread'` on Windows Python 3.14+.
"""
import asyncio
import asyncio.events as _aio_events


def ensure_event_loop() -> asyncio.AbstractEventLoop:
    target_classes = []
    base_cls = getattr(_aio_events, "BaseDefaultEventLoopPolicy", None)
    if base_cls is not None:
        target_classes.append(base_cls)
    active_cls = type(asyncio.get_event_loop_policy())
    if active_cls not in target_classes:
        target_classes.append(active_cls)

    for cls in target_classes:
        orig_fn = cls.get_event_loop
        if getattr(orig_fn, "__name__", "") != "_py314_safe_get_event_loop":
            def _make_wrapper(_orig):
                def _py314_safe_get_event_loop(self) -> asyncio.AbstractEventLoop:
                    local_obj = getattr(self, "_local", None)
                    if local_obj is not None and getattr(local_obj, "_loop", None) is None:
                        loop = self.new_event_loop()
                        self.set_event_loop(loop)
                        return loop
                    try:
                        return _orig(self)
                    except RuntimeError:
                        loop = self.new_event_loop()
                        self.set_event_loop(loop)
                        return loop

                return _py314_safe_get_event_loop

            cls.get_event_loop = _make_wrapper(orig_fn)  # type: ignore[method-assign]

    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.get_event_loop_policy().get_event_loop()


ensure_event_loop()
