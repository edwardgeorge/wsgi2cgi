#!/usr/bin/env perl
#
# Simple test CGI (prints environment variables).
#
print "Content-Type: text/plain\n\n";

foreach(keys(%ENV)) {
    print "$_ = $ENV{$_}\n";
}

