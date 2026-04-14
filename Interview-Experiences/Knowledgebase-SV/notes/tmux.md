## Tmux cheat sheet

By default the prefix key is Ctrl + B, I have changed it to Ctrl + Space

Access my tmux config at [link](https://github.com/Shivam5022/.dotfiles/blob/main/tmux.conf)

Some of the commands below are as per my configuration, which is different from the default ones.

### Sessions

1.  Start a new session

            tmux new -s <session-name>

2.  Attach to a session (from outside tmux)

            tmux attach -t <session-name>
            tmux a

3.  Detach from a session

            Press <PREFIX>, then d

4.  List sessions

            tmux ls

### Windows

We can have windows inside a session

1.  Create a new window

            Press <PREFIX>, then c

2.  Rename the current window:

            Press <PREFIX>, then ,

3.  Kill a window / session

            Press Ctrl+d

4.  Switch between sessions and windows

            Press <PREFIX>, then w
            Press <PREFIX>, then <window number>
            Press <PREFIX>, then p (previous window)
            Press <PREFIX>, then n (next window)

### Panes

In a window we can have multiple panes:

1.  Split horizontal

            Press <PREFIX>, then |

2.  Split vertically

            Press <PREFIX>, then _

3.  Switch between panes

            Press <PREFIX>, then <arrow keys>

### More

1.  Rename session

            tmux rename-session -t <old-name> <new-name>

2.  Kill all sessions

            tmux kill-server
