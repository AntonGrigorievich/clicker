import pygetwindow as gw


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
        return (self.left, self.top, self.width, self.height)

    def activate(self):
        try:
            self.win.activate()
        except Exception:
            pass

    def __repr__(self):
        return f"<GameWindow title='{self.win.title}' profile={self.profile}>"


class WindowProvider:
    def __init__(self, title_contains="Dogiators"):
        self.title_contains = title_contains

    def get_windows(self) -> list[GameWindow]:
        wins = gw.getWindowsWithTitle(self.title_contains)
        result = []

        for w in wins:
            if w.width > 200 and w.height > 200:
                result.append(GameWindow(w))

        return result
