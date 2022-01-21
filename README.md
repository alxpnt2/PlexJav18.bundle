# PlexJav18.bundle

Finds Japanese Adult Video (JAV) metadata for Plex from [R18.com](https://www.r18.com/). 

Alternatively, biscuitrainbow has a [fork](https://github.com/biscuitrainbow/PlexJav18.bundle) that fetches from javadatabase.com and www.141jav.com.

## Installation
Click [here](https://github.com/alxpnt2/PlexJav18.bundle/archive/master.zip) to download a zip file containing the latest version of plugin, or click the green "Clone or download" button above. Extract the Jav18.bundle folder from the zip file (within the PlexJav18.bundle-master folder) and place it in your Plex server's plugins folder. You can find out where that is [here](https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/). Close your Plex server and restart it, and it should be selectable as an agent (called "Jav18") in movie and video libraries.

## How to Use
It searches the R18 database using the release label and number associated with the video (e.g. XYZ-123). It gets this info from the filename, so ensure that your video files have it in their name. I use and have tested the following folder structure for my library:

```
JAV/
    ABC/
        ABC-123/
                ABC-123.mp4
        ABC-456/
                ABC-456 - pt1.mp4
                ABC-456 - pt2.mp4
    XYZ/
    ...
```

This is the only structure I've tested, but it shouldn't particularly matter as long as Plex can distinguish which files belong together and which don't.

R18 isn't 100% complete, so there may be some releases that won't retrieve metadata. JavLibrary seems to have a more complete database and includes some actor information that R18 doesn't, but as of yet I haven't found a good way of scraping that website.

## Credits
This plugin was based on PhoenixPlexCode's Data18-Phoenix.bundle plugin [here](https://github.com/PhoenixPlexCode/Data18-Phoenix.bundle). 

Uses biscuitrainbow's solution from their fork for generating high-res posters.
