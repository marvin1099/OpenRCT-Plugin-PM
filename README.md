# OpenRCT-Plugin-Downlader
Main repo: https://codeberg.org/marvin1099/OpenRCT-Plugin-PM  
Backup repo: https://github.com/marvin1099/OpenRCT-Plugin-PM  

This branch is a new way on how to grab the openrct plugins from the webside,  
using the implemented json request via url parameters.  
Right now Im not working on this but i figured i may as well upload the proof of concept.  
The Readme bellow is just the one of the old plugin downloader.  
As this is not done and probably wont be any time soon i will leave everything else as is.  
Chech the file orct-pldl.py for changes if intrested.  
The proof of concept in this branch only prints all found plugins for now.  
The proof of concept runs with pure python btw.


# Table of contents
[Description](#description)  
[Install](#install)  
[Usage](#usage)  

# Description
A somewhat structured portable OpenRCT plugin package manager and downloader written in python.  
The script gets all the plugins from the   
https://openrct2plugins.org/  
website by web-scraping and then from the github api.  
The new version is out now and the config is now changed so it is compatible with v0.5 and above.  
Keep in mind i used AI to help me make this.

# Install
First you need to download python and the python dependency   

    pip install beautifulsoup4  
Then get the script from  
[Codeberg Releases](https://codeberg.org/marvin1099/OpenRCT-Plugin-PM/releases)  
or get it from  
[Github Releases](https://github.com/marvin1099/OpenRCT-Plugin-PM/releases)  
Put the ```orct-cmd-plugin-dl.py``` in the openrct plugin folder  
Then run ```orct-cmd-plugin-dl.py``` inside the "openrct plugin folder"  
It is important that you run the script with the "openrct plugin folder" as working directory.  
This is so that the plugins and the config file all get written to the plugin folder.  
You can do this by openning a terminal inside the "openrct plugin folder".  
You can also open a terminal, type ```cd "openrct plugin folder path"``` and then run the file.  
For windows open the cmd and the cd command might need a /d, so ```cd /d "openrct plugin folder path"```.  

# Usage
    usage: orct-pldl.py [-h] [-q QUERY [QUERY ...]] [-n NUMBER]
    [-f {n,d,a,s,g,b,m,l,i,x,t,r,p} [{n,d,a,s,g,b,m,l,i,x,t,r,p} ...]]
    [-s {n,s,m,l,r} [{n,s,m,l,r} ...]] [-r REMOVE [REMOVE ...]] [-i INSTALL [INSTALL ...]]
    [-o] [-u] [-x] [-t] [-l] [-d] [-g IGNOREURL] [-c CONFIG]

    A simple OpenRCT plugin finder and downloader

    options:
    -h, --help            show this help message and exit
    -q QUERY [QUERY ...], --query QUERY [QUERY ...]
    search for an online database plugin
    -n NUMBER, --number NUMBER
    search for stars, submitted and last_updated (use g or b in fields to specifie max
    or min)
    -f {n,d,a,s,g,b,m,l,i,x,t,r,p} [{n,d,a,s,g,b,m,l,i,x,t,r,p} ...], --fields {n,d,a,s,g,b,m,l,i,x,t,r,p} [{n,d,a,s,g,b,m,l,i,x,t,r,p} ...]
    fields to search (n: name (default), d: description, a: author, s: stars, g: above,
    b: below, x: disable unixtime - number, m: submitted, l: license, i: url_identifier,
    t: tags, r: only query and number, p: enable partial tag search)
    -s {n,s,m,l,r} [{n,s,m,l,r} ...], --sort {n,s,m,l,r} [{n,s,m,l,r} ...]
    field to sort the results (n: for name, s: stars, m: submitted, l: last_updated, r:
    reverse results)
    -r REMOVE [REMOVE ...], --remove REMOVE [REMOVE ...]
    remove installed plugin
    -i INSTALL [INSTALL ...], --install INSTALL [INSTALL ...]
    install online database plugin
    -o, --ols             list indexed online plugins
    -u, --update          force update plugins (default auto update every 24 hours)
    -x, --idxup           force update plugin index (default auto update every hour)
    -t, --timeoutnow      enable instant timeout (recommended on multiple installs, will just grab the first
    file for all online files)
    -l, --ls              list installed plugins
    -d, --dignore         disable ignore list
    -g IGNOREURL, --ignoreurl IGNOREURL
    set ignore url
    -c CONFIG, --config CONFIG
    Config file to use (default: orct-pldl.json)