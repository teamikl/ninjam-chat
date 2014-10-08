
#!/bin/sh

err=3
while test "$err" -eq 3 ; do
    python3 bot.py
    err="$?"
    sleep 5
done
