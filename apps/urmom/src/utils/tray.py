import pystray
from PIL import Image
from .paths import get_asset_path


def create_icon(cleanup_func):
    def on_quit(icon, item):
        icon.stop()
        cleanup_func()

    # Define the menu
    menu = pystray.Menu(pystray.MenuItem("Quit", on_quit))

    icon = pystray.Icon(
        "urmom", Image.open(get_asset_path("mom.ico")), "UrMom Controller", menu
    )
    return icon
