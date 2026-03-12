# OpenRCT-Plugin-Downlader
Main repo: https://codeberg.org/marvin1099/OpenRCT-Plugin-PM  
Backup repo: https://github.com/marvin1099/OpenRCT-Plugin-PM  

# Table of contents
[Description](#description)  
[Install](#install)  
[Usage](#usage)  

# Description
A somewhat structured portable OpenRCT plugin package manager and downloader written in python.  
The script gets all the plugins from the   
https://openrct2plugins.org/  
using the openrct plugin api and then the github api.  
This version is compatible with v0.5 and above.  
Keep in mind i used AI to help me make this.

# Install
First you need to download python

Then get the script from  
[Codeberg Releases](https://codeberg.org/marvin1099/OpenRCT-Plugin-PM/releases)  
or get it from  
[Github Releases](https://github.com/marvin1099/OpenRCT-Plugin-PM/releases)  
Put the ```orct-pldl.py``` in the openrct plugin folder  
Then run ```orct-pldl.py``` inside the "openrct plugin folder"  
It is important that you run the script with the "openrct plugin folder" as working directory.  
This is so that the plugins and the config file all get written to the plugin folder.  
You can do this by openning a terminal inside the "openrct plugin folder".  
You can also open a terminal, type ```cd "openrct plugin folder path"``` and then run the file.  
For windows open the cmd and the cd command might need a /d, so ```cd /d "openrct plugin folder path"```.  

# Usage
    usage: orct-pldl.py [-h] [-q QUERY [QUERY ...]] [-n NUMBER] [-f {n,d,a,s,g,b,m,l,i,x,t,r,p} [{n,d,a,s,g,b,m,l,i,x,t,r,p} ...]]
    [-s {n,s,m,l,r} [{n,s,m,l,r} ...]] [-r REMOVE [REMOVE ...]] [-i INSTALL [INSTALL ...]] [-o] [-u] [-x] [-t] [-l]
    [-d] [-g IGNOREURL] [-c CONFIG]
    
    A simple OpenRCT plugin finder and downloader
    
    options:
    -h, --help            show this help message and exit
    -q, --query QUERY [QUERY ...]
    search for an online database plugin
    -n, --number NUMBER   search for stars, submitted and last_updated (use g or b in fields to specify max or min)
    -f, --fields {n,d,a,s,g,b,m,l,i,x,t,r,p} [{n,d,a,s,g,b,m,l,i,x,t,r,p} ...]
    fields to search (n: name (default), d: description, a: author, s: stars, g: above, b: below, x: disable
    unixtime - number, m: submitted, l: license, i: url_identifier, t: tags, r: only query and number, p: enable
    partial tag search)
    -s, --sort {n,s,m,l,r} [{n,s,m,l,r} ...]
    field to sort the results (n: for name, s: stars, m: submitted, l: last_updated, r: reverse results)
    -r, --remove REMOVE [REMOVE ...]
    remove installed plugin
    -i, --install INSTALL [INSTALL ...]
    install online database plugin
    -o, --ols             list indexed online plugins
    -u, --update          force update plugins (default auto update every 24 hours)
    -x, --idxup           force update plugin index (default auto update every hour)
    -t, --timeoutnow      enable instant timeout (recommended on multiple installs, will just grab the first file for all online files)
    -l, --ls              list installed plugins
    -d, --dignore         disable ignore list
    -g, --ignoreurl IGNOREURL
    set ignore url
    -c, --config CONFIG   Config file to use (default: orct-pldl.json)