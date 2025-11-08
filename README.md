
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

## iOS Color Palette

SwiftUI uses a centralized palette in `noon-ios/Noon/ColorPalette.swift`:

- `ColorPalette.Semantic` provides semantic `Color` values (primary, secondary, destructive, success, warning).
- `ColorPalette.Text` and `ColorPalette.Surface` cover common text and background tones.
- `ColorPalette.Gradients` exposes reusable gradients, including the orangey primary gradient for call-to-action elements.

Use these helpers rather than hard-coding colors to keep the interface consistent. For example:

```swift
Text("CTA")
    .foregroundStyle(ColorPalette.Text.inverted)
    .padding()
    .background(ColorPalette.Gradients.primary)
    .clipShape(Capsule())
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