## Cheat.sh

You can find important usage info about command line tools like grep, find,
curl etc at [cheat.sh](https://cheat.sh).

Here is a very minimal script for getting documentation about tools from
command line:

```sh
# Function to query cheat.sh and display results with less
cheat() {
    if [ -z "$1" ]; then
        echo "Usage: cheat <topic>"
        echo "Example: cheat grep"
        return 1
    fi

    local topic="$1"

    # Fetch the cheat sheet from cheat.sh
    echo "https://cheat.sh/${topic}"
    curl -s "https://cheat.sh/${topic}" | less -R
}
```

Add it in `.zshrc` and use like: `cheat grep`
