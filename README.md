# master-ubuntu
## Note for developers

This script is my first Python script.
All is not written according to the real pythonic way of coding...

## Why ?

This script makes it possible to automate the tasks to be performed after a fresh ubuntu installation therfore you can homogenize the configuration of several Ubuntu PCs.

This script allows you to:
- Update/upgrade
- Make a "virtual drive (TMPFS)" in order to store apt archives
- Disable the swap
- Install packages
- Fix Microsoft fonts setup
- Setup unity environment

You can use, modify, change, do your coffee,... ON YOUR OWN RISKS !!!
This script is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

## Install

Copy python script and json in your home directory.


## Command line options

`usage: sudo master_ubuntu_v1.0.py [-h] [-f FILE] [-o FILE] [-v] {all,menu,gui} ...`

Use `-h` option to get usage.

## Interface

We can:
- Launch all tasks with a progress bar
- Launch all tasks with log
- Select the task with a menu (terminal/console)
- Select the task with a GUI

When all the tasks are finished, you can check the log file (`/tmp/masterUbuntu.log`). The log file can be changed using the `-o` option.

## Settings

Settings are provided by `mysetup.json`. You can change this file according to your own needs.
You can define another file using `-f` option.

Please, if you change the options then follow these rules :
- Don't change the GUI part
- You can add/remove package but a package must be inside a category (Google, Dev ....)
- Inside a category, you must provide a key. This key must be unique.
```json
        "package": {
                "Google":{
                        "1": {
                                "KEY": "https://dl-ssl.google.com/linux/linux_signing_key.pub",
                                "LABEL": "Chrome",
                                "PKG": "google-chrome-stable",
                                "PPA": "http://dl.google.com/linux/chrome/deb/",
                                "function": "installPKG",
                                "run": true
                        }
                }
```                        
A package can be defined with:
- PPA name/URL
- PPA Key

Note: function option allow me to call the Python function according to my script.

## Ubuntu release
16.10 tested/validated
