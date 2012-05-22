#!/usr/bin/env python

from optparse import OptionParser
import sys, time, traceback

from libconfig import LibalertConfig
from libalert import LibraryAlert

try:
    # Parse command-line options
    parser = OptionParser()
    parser.add_option('-t', '--testing', action='store_true',
                      help='send email to admin rather than users')
    (options, args) = parser.parse_args()
    
    # Load config
    config_file = args[0] if args else 'config.ini'
    config = LibalertConfig(config_file)
    
    # Main code
    libalert = LibraryAlert(config)
    
    print "###################################################################"
    print "Libalert: %s" % time.strftime("%c")
    
    # Check for all users' loans
    loans,errors = libalert.check_loans(testing=options.testing)
    
    if errors:
        print "\nCompleted with %d errors:" % len(errors)
        print "\n\n".join(errors)
    else:
        print "\nCompleted successfully."
        with open("lastOK","w") as f:
            f.write("last OK at %s\n" % time.strftime("%c"))

except Exception as e:
    print "*** %s ***" % e
    print traceback.format_exc()
    sys.exit(1)

sys.exit(0)
