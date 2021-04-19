#!/usr/bin/python3
# encoding: utf-8
'''
download OKAPI HTML dumps for all or for specified wiki projects
'''
import os
import sys
import getopt
import time
import json
import requests
from requests.auth import HTTPBasicAuth


USERAGENT = "okapi_downlaoder.py/v0.1 (ops-dumps@wikimedia.org)"
# connect and read timeout
TIMEOUT = 20
# max number of seconds to spend on a single download, longer than that means something broken
MAX_REQUEST_TIME = 60 * 30

# FIXME use session objects, we'll want them I think. Will we?
# FIXME use logging instead of prints, sys.stderr; log all exceptions
# FIXME if file already exists, it's not re-downloaded, this is bad in the
#   case of a truncated/broken file, let's find out about that.
# Timing tests, how long does this take to run?
# Can/should I run it directly on one labstore host and rsync to the other(s)?
# If run directly on a labstore box, what about bandwidth throttling as done for rsync?


class Downloader():
    '''
    retrieve and stash dumps for one or more wikis
    '''
    def __init__(self, creds, settings, date=None):
        self.creds = creds
        self.settings = settings
        self.date = date
        if not date:
            self.date = time.strftime("%Y%m%d", time.gmtime())
        dumpdir = os.path.join(settings['baseoutdir'], self.date)
        os.makedirs(dumpdir, exist_ok=True)

    def get_wiki_list(self):
        '''
        via okapi api, get the list of all projects for which dumps are created
        and return it, or None on error
        '''
        headers = {'user-agent': USERAGENT, "Accept": "application/json"}
        try:
            # even without the timeout, same thing. and I only get the first 565816 bytes,
            # not even a full 1mb so what's up with that.
            response = requests.get(self.settings['wikilisturl'],
                                    auth=HTTPBasicAuth(self.creds['user'], self.creds['passwd']),
                                    headers=headers, timeout=TIMEOUT)

            if response.status_code != 200:
                sys.stderr.write("failed to get wiki list with response code %s (%s)\n" %
                                 (response.status_code, response.reason))
                return None
            try:
                json_contents = json.loads(response.content)
            except Exception:
                sys.stderr.write("failed to load json for wiki list\n")
                sys.stderr.write("got: %s\n" % response.content)
                return None
            # schema:
            # [
            #   {
            #      "name": "Авикипедиа",
            #      "dbName": "abwiki",
            #      "inLanguage": "ab",
            #      "size": "9MB",
            #      "url": "https://ab.wikipedia.org"
            #   },
            #   ...
            # ]
            wikilist = [entry['dbName'] for entry in json_contents if'dbName' in entry]
            if not wikilist:
                sys.stderr.write("empty list of wikis retrieved\n")
                sys.stderr.write("got: %s\n" % response.content)
                sys.exit(1)
            return wikilist
        except Exception:
            return None

    def get_outfile_name(self, wiki):
        '''
        produce a filename with wiki and date in it someplace
        '''
        return "{wiki}-{date}-OKAPI-HTML.json.gz".format(wiki=wiki, date=self.date)

    def get_outfile_path(self, wiki):
        '''
        given the (db) name of the wiki, return the path to the output file
        where the downloaded dujmp should be written
        '''
        path = os.path.join(self.settings['baseoutdir'], self.date,
                            self.get_outfile_name(wiki))
        return path

    def get_one_wiki_dump(self, wiki):
        '''
        download the dump for one wiki, but if the file is alreadu there, just return
        returns True on success, False on error
        '''
        outfile = self.get_outfile_path(wiki)
        if os.path.exists(outfile):
            return True

        headers = {'user-agent': USERAGENT, "Accept": "application/json"}
        try:
            with requests.get(os.path.join(self.settings['basedumpurl'], wiki),
                              auth=HTTPBasicAuth(self.creds['user'], self.creds['passwd']),
                              headers=headers, stream=True, timeout=TIMEOUT) as response:
                outfile_tmp = outfile + ".tmp"
                with open(outfile_tmp, 'wb') as outf:
                    start = time.time()
                    # fixme what do we think of this chunk size?
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        outf.write(chunk)
                        now = time.time()
                        if now - start > MAX_REQUEST_TIME:
                            # we're taking too long. network issues? whatever it is, just give up
                            sys.stderr.write("download of wiki " + wiki + "taking too long, giving up\n");
                            return False
                os.rename(outfile_tmp, outfile)
        except Exception:
            return False
        return True


    def get_wiki_dumps(self, wikis=None, verbose=False):
        '''
        download html dumps for all specified wikis
        '''
        errors = False
        if not wikis:
            if verbose:
                print("retrieving wiki list")
            wikis = self.get_wiki_list()
            if verbose:
                print("wiki list:", wikis)
        if not wikis:
            if verbose:
                print("error retrieving wikis list")
            errors = True
        first = True
        for wiki in wikis:
            if verbose:
                print("retrieving dump for", wiki)
            if first:
                first = False
            else:
                time.sleep(self.settings['wait'])
            result = self.get_one_wiki_dump(wiki)
            if not result:
                if verbose:
                    print("error from dump retrieval for", wiki)
                errors = True
        return not errors


def usage(message=None):
    '''display usage info about this script'''
    if message is not None:
        print(message)
    usage_message = """Usage: okapi_downloader.py [--wikis name[,name,...]]
         [--creds path-to-recds-file] [--settings path-to-settings-file]
         [--retries num] [--verbose]| --help

Arguments:

  --wikis    (-w):   comma-separated list of names of the wiki dbs to download
                     default: None (download all)
  --creds    (-c):   path to plain text file with HTTP Basic Auth credentials
                     format: two lines, varname=value, with the varnames user and passwd
                             blank lines and those starting with '#' are skipped
                     default: .okapi_creds in current working directory
  --settings (-s):   path to settings file
                     format: two lines, varname=value, with the varnames wikilisturl,
                             outputdir, and dumpsurl; see the sample file in this repo
                             for each setting and its default value
                             blank lines and those starting with '#' are skipped
                     default: okapi-downloader_settings in current working directory
  --retries  (-r):   number of retries in case downloads fail
                     default: 0 (don't retry)
  --vernbose (-v):   show some progress messages while running
  --help     (-h):   display this usage message
"""
    print(usage_message)
    sys.exit(1)


def get_args():
    '''
    get and validate command-line args and return them
    '''
    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "c:r:s:w:vh", ["creds=", "settings=", "retries=", "wikis=",
                                         "verbose", "help"])

    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))

    args = {'retries': 0, 'wikis': None, 'verbose': False}

    for (opt, val) in options:
        if opt in ["-c", "--creds"]:
            args['creds'] = val
        elif opt in ["-w", "--wikis"]:
            args['wikis'] = val.split(',')
        elif opt in ["-w", "--settings"]:
            args['settings'] = val
        elif opt in ["-r", "--retries"]:
            if not val.isdigit():
                usage('Retries value must be a number')
            args['retries'] = int(val)
        elif opt in ["-v", "--verbose"]:
            args['verbose'] = True
        elif opt in ["-h", "--help"]:
            usage('Help for this script')
        else:
            usage("Unknown option specified: <%s>" % opt)

    if remainder:
        usage("Unknown option(s) specified: {opt}".format(opt=remainder[0]))

    return args


def get_creds(filepath):
    '''
    read path and return values for user, passwd
    '''
    user = None
    passwd = None
    if not os.path.exists(filepath):
        usage("Failed to find credentials file: " + filepath)
    contents = open(filepath).read()
    entries = contents.splitlines()
    for entry in entries:
        if entry.startswith('#'):
            continue
        entry = entry.strip()
        if not entry:
            continue
        if not '=' in entry:
            usage("Bad format for credentials in " + filepath)
        name, value = entry.split('=', 1)
        if name == 'user':
            user = value
        elif name == 'passwd':
            passwd = value
        else:
            usage("Unknown entry in credentials file " + filepath)
    if not user or not passwd:
        usage("Both user and passwd must be specified in credntials file")
    return user, passwd


def get_settings(filepath):
    '''
    read path and return values for various settings, fallinf back to defaults
    if they are not in the file
    '''
    settings = {
        'wikilisturl': "https://api.wikimediaenterprise.org/v1/projects",
        'basedumpurl': "https://api.wikimediaenterprise.org/v1/exports/json",
        'baseoutdir':  "/home/ariel/wmf/okapi/downloader/test",
        'wait': 20,
        'retrywait': 10,
        }
    int_settings = ['wait', 'retrywait']
    contents = open(filepath).read()
    entries = contents.splitlines()
    for entry in entries:
        if entry.startswith('#'):
            continue
        entry = entry.strip()
        if not entry:
            continue
        if not '=' in entry:
            usage("Bad format for setting " + entry + " in " + filepath)
        name, value = entry.split('=', 1)
        if name not in settings.keys():
            usage("Unknown entry " + entry + " in settings file " + filepath)
        if name in int_settings:
            settings[name] = int(value)
        else:
            settings[name] = value
    return settings


def do_main():
    '''entry point'''
    args = get_args()
    credspath = args.get('creds', os.path.join(os.getcwd(), '.okapi_creds'))

    user, passwd = get_creds(credspath)
    if not user or not passwd:
        usage("username and password file must be set up")
    if args['verbose']:
        print("Credentuials retrieved")
    creds = {'user': user, 'passwd': passwd}

    if 'settings' in args:
        settingspath = args['settings']
        if not os.path.exists(settingspath):
            usage('Failed to find specified settings file ' + settingspath)
    else:
        settingspath = os.path.join(os.getcwd(), 'okapi_downloader_settings')
    settings = get_settings(settingspath)

    downloader = Downloader(creds, settings)

    retries = 0
    while retries <= args['retries']:
        if 'wikis' in args:
            errors = downloader.get_wiki_dumps(args['wikis'], verbose=args['verbose'])
        else:
            errors = downloader.get_wiki_dumps(verbose=args['verbose'])
        if not errors:
            break
        retries += 1
        if retries < args['retries']:
            if args['verbose']:
                print("sleeping for", settings['retrywait'], "minutes before retry of failed wikis")
            time.sleep(settings['retrywait'] * 60)


if __name__ == '__main__':
    do_main()
