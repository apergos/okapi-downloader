Okapi Downloader
====================

This is still incomplete. In fact it won't even download a complete file.
You have been warned.

The filenames, classes, and every other thing in here might change overnight.
But better to be stashed here than not be backed up someplace.

Setup
--------------------
Get Okapi credentials from your friendly provider, and stash them into a file
called .okapi_creds in the durectory where this script is located. See
.okapi_creds.sample for the format.

Copy okapi_downloader_settings.sample into okapi_downloader_settings and adjust
the baseoutdir and the retrywait times to suit. Be nice to the servers.
Make sure the baseoutdir actually exists.

If you're running your own copy of this script, which I assume you are,
change the USERAGENT in okapi_downloader.py to have your email address.
That way the Okapi folks can contact you if there is a problem.

Running
--------------------
You can get a nice help message with
python3 ./okapi_downloader.py --help

You will most likely be interested in only a few wikis. Get them via
python3 ./okapi_downloader.py --wikis firstwiki,secondwiki,...

That is all.


