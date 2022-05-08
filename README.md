# PlexJav18.bundle

Finds Japanese Adult Video (JAV) metadata for Plex from [R18.com](https://www.r18.com/) and 141JAV. 

## Installation
Click [here](https://github.com/alxpnt2/PlexJav18.bundle/archive/master.zip) to download a zip file containing the latest version of plugin, or click the green "Clone or download" button above. Extract the Jav18.bundle folder from the zip file (within the PlexJav18.bundle-master folder) and place it in your Plex server's plugins folder. You can find out where that is [here](https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/). Close your Plex server and restart it, and it should be selectable as an agent (called "Jav18") in movie and video libraries.

## How to Use
It searches the 141JAV databases using the release label and number associated with the video (e.g. XYZ-123). It gets this info from the filename, so ensure that your video files have it in their name. If the release is found, it then consults AV-Wiki.net to find the FANZA ID for that release, which is how titles are catalogued on R18. If there is none or R18 doesn't have it listed, then 141JAV is used as a backup for metadata.

I use and have tested the following folder structure for my library:

```
JAV/
    ABC/
        ABC-123.mp4
        ABC-456 - pt1.mp4
        ABC-456 - pt2.mp4
    XYZ/
    ...
```

This is the only structure I've tested, but it shouldn't particularly matter as long as Plex can distinguish which files belong together and which don't.

R18 isn't 100% complete, so there may be some releases that won't have their full metadata. If no data can be found on R18, 141JAV is used as a backup, but it has much less to work with. 

JavLibrary seems to have a more complete database, but as of yet I haven't found a good way of scraping that website.

## Troubleshooting
### How do I pick which sites are used for searching?
Go to the Manage Library page for your Jav18 library and select Advanced. There are several options available. By default, 141Jav and R18 are the only ones enabled, but if you're not getting any results, you can try to enable the others. Note: These settings only change which options show up when matching. When compiling metadata, all possible sites are checked.

### Can I change the title language?
R18 supports both English and Chinese, so you can pick which language you would like to use in the Manage Library settings. This only affects data scraped from R18.

### Why aren't I getting any metadata?
Make sure that you are using the correct folder structure (see above) and that your videos are named for the release number (ABC-123.mp4). If your videos are named correctly and still aren't having metadata populated for them, make sure that you can find them on R18 and 141JAV.

### I'm getting title information, but the poster isn't loading or the poster is low res.
The API that generates the high-res poster doesn't have 100% up-time, so if you're getting a low-res poster, try waiting a few minutes and trying again. 

### I'm still not getting the right poster or my metadata isn't loading.
If there isn't already an issue written up for your problem on the issues tab, write one up and attach your Jav18 plug-in log to the issue. Find the log folder using [this support article](https://support.plex.tv/articles/200250417-plex-media-server-log-files/). Once you are in the log folder, navigate into `PMS Plugin Logs` and grab the file called `com.plexapp.agents.jav18.log`.

## Credits
This plugin was based on PhoenixPlexCode's Data18-Phoenix.bundle plugin [here](https://github.com/PhoenixPlexCode/Data18-Phoenix.bundle).
