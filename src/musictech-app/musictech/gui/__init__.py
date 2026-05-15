"""GUI placeholder.

The pygame-based UI (``interactive_tester.py``, 5 KLOC) is the main
end-user entry point. It depends on every other module here. We
**explicitly do not refactor it** in this pass: any reshuffle breaks
playback, and the design is going to be replaced anyway by the C++
shell described in the project plan.

New GUI work belongs to that C++ application, not here.
"""

__all__: list[str] = []
