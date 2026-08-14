# Python User Packages PATH Setup

## Problem

When using Neovim with linters like `flake8`, you may encounter errors:

```
Error running flake8: ENOENT: no such file or directory
```

This happens because Python user-installed packages (via `pip install --user` or when site-packages is not writable) are
installed to `~/Library/Python/<version>/bin/` on macOS, which is not in the default PATH.

## Solution

Add the Python user bin directory to your PATH in `~/.zshrc`:

```bash
# Python user packages
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

Then reload your shell:

```bash
source ~/.zshrc
```

## Verification

Check that flake8 (or other tools) are now accessible:

```bash
which flake8
flake8 --version
```

## Notes

- Replace `3.9` with your Python version if different
- This applies to any pip-installed command-line tools (flake8, black, mypy, etc.)
- Check your Python version with: `python3 --version`
- Find where pip installs user packages: `python3 -m site --user-base`

## Related

- [pip user installs documentation](https://pip.pypa.io/en/stable/user_guide/#user-installs)
