import pygetwindow as gw


class WindowProviderWindows:
    def __init__(self, title_contains="Dogiators"):
        self.title_contains = title_contains

    def get_windows(self):
        wins = gw.getWindowsWithTitle(self.title_contains)
        return [w for w in wins if w.width > 200 and w.height > 200]
