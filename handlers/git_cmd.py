from config import ALLOWED_GIT_SUBCOMMANDS


def validate_git_command(args: list[str]) -> str | None:
    """Validate git subcommand. Returns error message or None if valid."""
    if not args:
        return "git requires a subcommand."

    subcommand = args[0]
    if subcommand not in ALLOWED_GIT_SUBCOMMANDS:
        return (
            f"git subcommand `{subcommand}` is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_GIT_SUBCOMMANDS))}"
        )
    return None
