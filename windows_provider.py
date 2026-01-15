import platform

from windows_provider_mac import WindowProviderMac
from windows_provider_win import WindowProviderWindows


class GameWindow:
    def __init__(self, win, profile=None):
        self.win = win
        self.profile = profile

    @property
    def left(self):
        return self.win.left

    @property
    def top(self):
        return self.win.top

    @property
    def width(self):
        return self.win.width

    @property
    def height(self):
        return self.win.height

    @property
    def region(self):
        return (
            max(0, self.left),
            max(0, self.top),
            self.width,
            self.height
        )

    def activate(self):
        try:
            self.win.activate()
        except Exception:
            pass

    def __repr__(self):
        return f"<GameWindow title='{self.win.title}' profile={self.profile}>"


class WindowProvider:
    def __init__(self, title_contains="Dogiators"):
        if platform.system() == "Darwin":
            self.provider = WindowProviderMac(title_contains)
        else:
            self.provider = WindowProviderWindows(title_contains)

    def get_windows(self) -> list[GameWindow]:
        return [
            GameWindow(w)
            for w in self.provider.get_windows()
        ]
