import Quartz
import AppKit


class MacWin:
    def __init__(self, title, x, y, w, h):
        self.title = title
        self.left = x
        self.top = y
        self.width = w
        self.height = h

    def activate(self):
        pass 


class WindowProviderMac:
    def __init__(self, title_contains="Dogiators"):
        self.title_contains = title_contains.lower()

    def get_windows(self):
        windows = []

        opts = (
            Quartz.kCGWindowListOptionOnScreenOnly |
            Quartz.kCGWindowListExcludeDesktopElements
        )

        window_list = Quartz.CGWindowListCopyWindowInfo(
            opts,
            Quartz.kCGNullWindowID
        )

        screen = AppKit.NSScreen.mainScreen()
        screen_height = screen.frame().size.height
        scale = screen.backingScaleFactor()


        for win in window_list:
            owner = (win.get("kCGWindowOwnerName") or "").lower()
            title = (win.get("kCGWindowName") or "").lower()

            if self.title_contains not in f"{owner} {title}":
                continue

            bounds = win.get("kCGWindowBounds")
            if not bounds:
                continue

            x = int(bounds["X"])
            y = int((screen_height - bounds["Y"] - bounds["Height"]))
            w = int(bounds["Width"])
            h = int(bounds["Height"])
            # x = int(bounds["X"] * scale)
            # y = int((screen_height - bounds["Y"] - bounds["Height"]) * scale)
            # w = int(bounds["Width"] * scale)
            # h = int(bounds["Height"] * scale)

            if w < 200 or h < 200:
                continue

            windows.append(
                MacWin(title or owner, x, y, w, h)
            )

        return windows
