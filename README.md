Wikimedia Enterprise Downloader
===============================

This is not production ready but is ok for testing purposes.

Setup
--------------------
Get Wikimedia Enterprise credentials from your friendly provider, and stash them into a file
called .wm_enterprise_creds in the durectory where this script is located. See
.wm_enterprise_creds.sample for the format.

Copy wm_enterprise_settings.sample into wm_enterprise_downloader_settings and adjust
the baseoutdir and the retrywait times to suit. Be nice to the servers. Make sure the baseoutdir
actually exists.

If you're running your own copy of this script, which I assume you are, change the USERAGENT
in wm_enterprise_downloader.py to have your email address. That way the Wikimedia Enterprise folks
can contact you if there is a problem.

Running
--------------------
You can get a nice help message with
python3 ./wm_enterprise_downloader.py --help

You will most likely be interested in only a few wikis in namespace 0. Get them one at a time via
python3 ./wm_enterprise_downloader.py --wiki somewiki --namespace 0
