"""Steam Remote Play configuration — game allowlist and protocol URLs."""

__all__ = [
    "STEAM_GAMES",
    "STEAM_APP_PATH",
]

STEAM_APP_PATH = "/Applications/Steam.app"

# display_name -> Steam App ID (from store.steampowered.com/app/<id>)
# Add your installed games here
STEAM_GAMES: dict[str, int] = {
    # "Counter-Strike 2": 730,
    # "Stardew Valley": 413150,
}
