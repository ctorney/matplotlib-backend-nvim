# SPDX-License-Identifier: CC0-1.0

import os
import sys
import tempfile
import warnings
from io import BytesIO
from subprocess import run

from matplotlib import interactive, is_interactive
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import FigureManagerBase, _Backend
from matplotlib.backends.backend_agg import FigureCanvasAgg

# XXX heuristic for interactive repl
if sys.flags.interactive:
    interactive(True)

TRANSPARENT = os.getenv('MPLBACKEND_TRANSPARENT', '0').lower()
TRANSPARENT = bool(TRANSPARENT == 'true' or TRANSPARENT == '1')


class FigureManagerTerminal(FigureManagerBase):
    def __init__(self, canvas, num):
        self.img = None

        super().__init__(canvas, num)

    def show(self):
        try:
            if self.img is not None:
                self.img.close()

            self.img = tempfile.NamedTemporaryFile(buffering=0, suffix='.png')
            self.canvas.figure.savefig(
                self.img, format='png', transparent=TRANSPARENT, dpi=300, bbox_inches='tight', pad_inches=0.4
            )
            print('![terminalimage](' + self.img.name + ')')

        except FileNotFoundError:
            warnings.warn('Unable to plot to terminal.')


class FigureCanvasTerminal(FigureCanvasAgg):
    manager_class = FigureManagerTerminal


@_Backend.export
class _BackendTerminalAgg(_Backend):
    FigureCanvas = FigureCanvasTerminal
    FigureManager = FigureManagerTerminal

    # Noop function instead of None signals that
    # this is an "interactive" backend
    mainloop = lambda: None

    # XXX: `draw_if_interactive` isn't really intended for
    # on-shot rendering. We run the risk of being called
    # on a figure that isn't completely rendered yet, so
    # we skip draw calls for figures that we detect as
    # not being fully initialized yet. Our heuristic for
    # that is the presence of axes on the figure.
    @classmethod
    def draw_if_interactive(cls):
        manager = Gcf.get_active()
        if is_interactive() and manager.canvas.figure.get_axes():
            cls.show()

    @classmethod
    def show(cls, *args, **kwargs):
        _Backend.show(*args, **kwargs)
        Gcf.destroy_all()
