
```
   _   _    .-----.  .-----.    _   _
  | \ | |  / 12 ^ \ / 12 ^ \  | \ | |
  |  \| | |  \ |  ||  | /  | |  \| |
  | |\  | |  / o  ||  o \  | | |\  |
  |_| \_|  \__6__/  \__6__/  |_| \_|

  it's time, but it's really simple.
```


## Development

Make sure you have [uv](https://docs.astral.sh/uv) installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Usage:

```bash
# To format
uv run ruff format

# To lint
uv run ruff check

# To auto-fix lint issues
uv run ruff check --fix

# To add dependencies
uv add anthropic

# To sync your env
uv sync

# To run a script
uv run