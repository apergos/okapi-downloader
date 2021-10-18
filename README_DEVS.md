Wikimedia Enterprise Downloader
===============================

Testing
--------------------
For testing, you may download one specific wiki; see the regular README for how to do that.
YOu may also download a slice of the list of wikis for all namespaces, which will cause
the script to do all of its regular work, downloading the list of namespaces, downloading
the list of wikis for each namespace, and then dumping the specific list subset for each
namespace.

Example:
python3 ./wm_enterprise_downloader.py  --test 5,6 --verbose 
At the time this README was written, afwikiquote was the one wiki that was downloaded, and only
for namespace 0, a nice short test.

For settings and credentials, see the regular README.

Design notes
--------------------
The script writes a "dump info" file, consisting of the md5hash and the date modified
for the dump output file, in json format, and the dump output file itself, into a file
in a subdirectory YYYYMMDD of the base directory specified in the settings file.

All errors are logged to stderr (the place that the standard python stream logger sends
them). These should be collected by cron or a systemd timer and emailed at periodic
intervals to a suitable email alias, so that dump maintainers can look into the problem.

The script is designed to be as resilient as possible; if a single wiki fails, the script will
log the errors to stderr and continue on. If more than 5 wikis fail in a row, the script
will consider that as a failed run, sleep for awhile, and retry the run. Any dumps that were
successfully downloaded will be kept and not retried or overwritten.
If 5 retries of the run fail, the script will give up; at this point it is expected that
a human should intervene.
