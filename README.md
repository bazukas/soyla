# About

This is a simple client application for recording speech dataset given a file with text lines.
I made this program for myself so it might not suit your needs, feel free to open an issue
to request a feature.

![Program interface](img/soyla.png)

## Features

* record audio
* play audio
* edit text
* keep track of recorded lines

# Installing

`pip3 install soyla`

# Using

`python3 -m soyla `*`path_to_lines_file`*` `*`path_to_wavs_dir`*

# Warning

This program has not been tested thoroughly, so if you're going to use it,
then make sure to back up your lines file, since the program rewrites that
file each time you make changes to a text.
