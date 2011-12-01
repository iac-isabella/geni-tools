#!/usr/bin/python

#----------------------------------------------------------------------
# Copyright (c) 2011 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------
""" Acceptance tests for AM API v1."""

import datetime
from geni.util import rspec_util 
import unittest
import omni_unittest as ut
import os
import pprint
import re
import time

# TODO: TEMPORARILY USING PGv2 because test doesn't work with any of the others
# Works at PLC
RSPEC_NAME = "ProtoGENI"
RSPEC_NUM = 2
#RSPEC_NAME = "GENI"
#RSPEC_NUM = 3

# TODO: TEMPORARILY USING PGv2 because test doesn't work with any of the others
AD_NAMESPACE = "http://www.protogeni.net/resources/rspec/2"
AD_SCHEMA = "http://www.protogeni.net/resources/rspec/2/ad.xsd"
#GENI_AD_NAMESPACE = "http://www.geni.net/resources/rspec/3"
#GENI_AD_SCHEMA = "http://www.geni.net/resources/rspec/3/ad.xsd"
REQ_NAMESPACE = "http://www.protogeni.net/resources/rspec/2"
REQ_SCHEMA = "http://www.protogeni.net/resources/rspec/2/request.xsd"
#GENI_REQ_NAMESPACE = "http://www.geni.net/resources/rspec/3"
#GENI_REQ_SCHEMA = "http://www.geni.net/resources/rspec/3/request.xsd"
MANIFEST_NAMESPACE = "http://www.protogeni.net/resources/rspec/2"
MANIFEST_SCHEMA = "http://www.protogeni.net/resources/rspec/2/manifest.xsd"
#GENI_MANIFEST_NAMESPACE = "http://www.geni.net/resources/rspec/3"
#GENI_MANIFEST_SCHEMA = "http://www.geni.net/resources/rspec/3/manifest.xsd"

TMP_DIR="."
REQ_RSPEC_FILE="request.xml"
SLEEP_TIME=3
################################################################################
#
# Test AM API v1 calls for accurate and complete functionality.
#
# This script relies on the unittest module.
#
# To run all tests:
# ./am_api_v1_accept.py -l ../omni_accept.conf -c <omni_config> -a <AM to test>
#
# To run a single test:
# ./am_api_v1_accept.py -l ../omni_accept.conf -c <omni_config> -a <AM to test> Test.test_getversion
#
# To add a new test:
# Create a new method with a name starting with 'test_".  It will
# automatically be run when am_api_v1_accept.py is called.
#
################################################################################

# This is the acceptance test for AM API version 1
API_VERSION = 1

class Test(ut.OmniUnittest):
    """Acceptance tests for GENI AM API v1."""



    def test_GetVersion(self):
        """Passes if a 'GetVersion' returns an XMLRPC struct containing 'geni_api = 1'.
        """
        # Do AM API call
        omniargs = ["getversion"]
        (text, ret_dict) = self.call(omniargs, self.options_copy)

        pprinter = pprint.PrettyPrinter(indent=4)
        # If this isn't a dictionary, something has gone wrong in Omni.  
        ## In python 2.7: assertIs
        self.assertTrue(type(ret_dict) is dict,
                        "Return from 'GetVersion' " \
                        "expected to contain dictionary" \
                        "but instead returned:\n %s"
                        % (pprinter.pformat(ret_dict)))
        # An empty dict indicates a misconfiguration!
        self.assertTrue(ret_dict,
                        "Return from 'GetVersion' " \
                        "expected to contain dictionary keyed by aggregates " \
                        "but instead returned empty dictionary. " \
                        "This indicates there were no aggregates checked. " \
                        "Look for misconfiguration.")
        # Checks each aggregate
        for (agg, ver_dict) in ret_dict.items():
            ## In python 2.7: assertIsNotNone
            self.assertTrue(ver_dict is not None,
                          "Return from 'GetVersion' at aggregate '%s' " \
                          "expected to be XML-RPC struct " \
                          "but instead returned None." 
                           % (agg))
            self.assertTrue(type(ver_dict) is dict,
                          "Return from 'GetVersion' at aggregate '%s' " \
                          "expected to be XML-RPC struct " \
                          "but instead returned:\n %s" 
                          % (agg, pprinter.pformat(ver_dict)))
            self.assertTrue(ver_dict,
                          "Return from 'GetVersion' at aggregate '%s' " \
                          "expected to be non-empty XML-RPC struct " \
                          "but instead returned empty XML-RPC struct." 
                           % (agg))
            ## In python 2.7: assertIn
            self.assertTrue('geni_api' in ver_dict,
                          "Return from 'GetVersion' at aggregate '%s' " \
                          "expected to include 'geni_api' " \
                          "but did not. Returned:\n %s:"  
                           % (agg, pprinter.pformat(ver_dict)))
            value = ver_dict['geni_api']
            self.assertTrue(type(value) is int,
                          "Return from 'GetVersion' at aggregate '%s' " \
                          "expected to have 'geni_api' be an integer " \
                          "but instead 'geni_api' was of type %r." 
                           % (agg, type(value)))
            self.assertEqual(value, API_VERSION,
                          "Return from 'GetVersion' at aggregate '%s' " \
                          "expected to have 'geni_api=%d' " \
                          "but instead 'geni_api=%d.'"  
                           % (agg, API_VERSION, value))

    def test_ListResources(self, slicename=None):
        """Passes if 'ListResources' returns an advertisement RSpec (an XML document which passes rspeclint).
        """
        self.subtest_ListResources( slicename=slicename )

#     def test_ListResources_badCredential(self, slicename=None):
#         """Passes if 'ListResources' FAILS to return an advertisement RSpec when using a bad credential.
#         """
# #        self.options_copy
#         subtest_ListResources( slicename=slicename )


    def subtest_ListResources(self, slicename=None):
        # Check to see if 'rspeclint' can be found before doing the hard (and
        # slow) work of calling ListResources at the aggregate
        if self.options_copy.rspeclint:
            rspec_util.rspeclint_exists()

        if slicename:
            rspec_namespace = MANIFEST_NAMESPACE
            rspec_schema = MANIFEST_SCHEMA
        else:
            rspec_namespace = AD_NAMESPACE
            rspec_schema = AD_SCHEMA

        
        # Do AM API call
        if slicename:
            omniargs = ["listresources", str(slicename), "-t", str(RSPEC_NAME), str(RSPEC_NUM)]
        else:
            omniargs = ["listresources", "-t", str(RSPEC_NAME), str(RSPEC_NUM)]
        self.options_copy.omnispec = False # omni will complaining if both true
        (text, ret_dict) = self.call(omniargs, self.options_copy)

        pprinter = pprint.PrettyPrinter(indent=4)
        # If this isn't a dictionary, something has gone wrong in Omni.  
        ## In python 2.7: assertIs
        self.assertTrue(type(ret_dict) is dict,
                        "Return from 'ListResources' " \
                        "expected to contain dictionary " \
                        "but instead returned:\n %s"
                        % (pprinter.pformat(ret_dict)))
        # An empty dict indicates a misconfiguration!
        self.assertTrue(ret_dict,
                        "Return from 'ListResources' " \
                        "expected to contain dictionary keyed by aggregates " \
                        "but instead returned empty dictionary. " \
                        "This indicates there were no aggregates checked. " \
                        "Look for misconfiguration.")

        # Checks each aggregate
        for ((agg_name, agg_url), rspec) in ret_dict.items():
            ## In python 2.7: assertIsNotNone
            self.assertTrue(rspec is not None,
                          "Return from 'ListResources' at aggregate '%s' " \
                          "expected to be XML file " \
                          "but instead returned None." 
                           % (agg_name))
            # TODO: more elegant truncation
            self.assertTrue(type(rspec) is str,
                          "Return from 'ListResources' at aggregate '%s' " \
                          "expected to be string " \
                          "but instead returned: \n" \
                          "%s\n" \
                          "... edited for length ..." 
                          % (agg_name, rspec[:100]))

            # Test if file is XML and contains "<rspec" or "<resv_rspec"
            # TODO is_rspec_string() might not be exactly the right thing here
            self.assertTrue(rspec_util.is_rspec_string( rspec ),
                          "Return from 'ListResources' at aggregate '%s' " \
                          "expected to be XML " \
                          "but instead returned: \n" \
                          "%s\n" \
                          "... edited for length ..." 
                           % (agg_name, rspec[:100]))

            # Test if XML file passes rspeclint
            if self.options_copy.rspeclint:
                self.assertTrue(rspec_util.validate_rspec( rspec, 
                                                       namespace=rspec_namespace, 
                                                       schema=rspec_schema ),
                            "Return from 'ListResources' at aggregate '%s' " \
                            "expected to pass rspeclint " \
                            "but did not. Return was: " \
                            "\n%s\n" \
                            "... edited for length ..."
                            % (agg_name, rspec[:100]))

    def test_CreateSliver(self):
        """Passes if the sliver creation workflow succeeds:
        (1) (opt) createslice
        (2) createsliver
        (3) deletesliver
        (4) (opt) deleteslice
        """

        slice_name = self.create_slice_name()

        print slice_name
        # if reusing a slice name, don't create (or delete) the slice
        if not self.options_copy.reuse_slice_name:
            self.subtest_createslice( slice_name )
            time.sleep(SLEEP_TIME)

        self.subtest_CreateSliver( slice_name )
        # Always DeleteSliver
        try:
            time.sleep(SLEEP_TIME)
            self.subtest_DeleteSliver( slice_name )
        except AssertionError:
            raise
        except:
            pass                

        if not self.options_copy.reuse_slice_name:
            self.subtest_deleteslice( slice_name )


    def subtest_CreateSliver(self, slice_name):
        # Check for the existance of the Request RSpec file
        self.assertTrue( os.path.exists(self.options_copy.rspec_file),
                         "Request RSpec file, '%s' for 'CreateSliver' call " \
                             "expected to exist " \
                             "but does not." 
                         % self.options_copy.rspec_file )
        
        # CreateSliver
        omniargs = ["createsliver", slice_name, str(self.options_copy.rspec_file), "-t", RSPEC_NAME, RSPEC_NUM]
        text, manifest = self.call(omniargs, self.options_copy)

        pprinter = pprint.PrettyPrinter(indent=4)
        ## In python 2.7: assertIsNotNone
        self.assertTrue(manifest is not None,
                          "Return from 'CreateSliver'" \
                          "expected to be XML file " \
                          "but instead returned None.")
        # TODO: more elegant truncation
        self.assertTrue(type(manifest) is str,
                        "Return from 'CreateSliver' " \
                            "expected to be string " \
                            "but instead returned: \n" \
                            "%s\n" \
                            "... edited for length ..." 
                        % (manifest[:100]))

        # Test if file is XML and contains "<rspec" or "<resv_rspec"
        # TODO is_rspec_string() might not be exactly the right thing here
        self.assertTrue(rspec_util.is_rspec_string( manifest ),
                        "Return from 'CreateSliver' " \
                            "expected to be XML " \
                            "but instead returned: \n" \
                            "%s\n" \
                            "... edited for length ..." 
                        % (manifest[:100]))


    def subtest_DeleteSliver(self, slice_name):
        omniargs = ["deletesliver", slice_name]
        text, (successList, failList) = self.call(omniargs, self.options_copy)
        _ = text # Appease eclipse
        succNum, possNum = omni.countSuccess( successList, failList )
        _ = possNum # Appease eclipse
        # we have reserved resources on exactly one aggregate
        self.assertTrue( int(succNum) == 1, 
                         "Failed to delete sliver")


    def subtest_createslice(self, slice_name ):
        """Create a slice. Not an AM API call."""
        omniargs = ["createslice", slice_name]
        text, urn = self.call(omniargs, self.options_copy)
        _ = text # Appease eclipse
        self.assertTrue( urn, 
                         "Slice creation FAILED.")

    def subtest_deleteslice(self, slice_name):
        """Delete a slice. Not an AM API call."""
        omniargs = ["deleteslice", slice_name]
        text, successFail = self.call(omniargs, self.options_copy)
        _ = text # Appease eclipse
        self.assertTrue( successFail, 
                         "Delete slice FAILED.")

    # def test_ListResources2(self):
    #     """Passes if the sliver creation workflow succeeds:
    #     (1) (opt) createslice
    #     (2) createsliver
    #     (3) listresources <slice name>
    #     (4) [not implemented] sliverstatus
    #     (5) [not implemented] renewsliver (in a manner that should fail)
    #     (6) [not implemented] renewslice (to make sure the slice does not expire before the sliver expiration we are setting in the next step)
    #     (7) [not implemented] renewsliver (in a manner that should succeed)
    #     (8) deletesliver
    #     (9) (opt) deleteslice
    #     """

    #     slice_name = self.create_slice_name()

    #     if not self.options_copy.reuse_slice_name:
    #         self.subtest_createslice( slice_name )
    #         time.sleep(SLEEP_TIME)

    #     #         try:
    #     self.subtest_CreateSliver( slice_name )
    #     try:
    #         self.test_ListResources( slicename=slice_name )
    #         # self.subtest_sliverstatus( slice_name )
    #         # self.subtest_renewsliver_fail( slice_name )
    #         # self.subtest_renewslice_success( slice_name )
    #         # self.subtest_renewsliver_success( slice_name )
    #     except:
    #         raise
    #     finally:
    #         # Always DeleteSliver
    #         try:
    #             time.sleep(SLEEP_TIME)
    #             self.subtest_DeleteSliver( slice_name )
    #         except AssertionError:
    #             raise
    #         except:
    #             pass                

    #     # Always deleteslice
    #     if not self.options_copy.reuse_slice_name:
    #         self.subtest_deleteslice( slice_name )


if __name__ == '__main__':
    import sys
    import omni
    parser = omni.getParser()
    parser.add_option( "--reuse-slice", 
                       action="store", type='string', dest='reuse_slice_name', 
                       help="Use slice name provided instead of creating/deleting a new slice")
    parser.add_option( "--rspec-file", 
                       action="store", type='string', 
                       dest='rspec_file', default=REQ_RSPEC_FILE,
                       help="In CreateSliver tests, use request RSpec file provided instead of default of '%s'" % REQ_RSPEC_FILE )
    parser.add_option( "--rspeclint", 
                       action="store_true", 
                       dest='rspeclint', default=False,
                       help="Validate RSpecs using 'rspeclint'" )

    usage = "\n      %s -a am-undertest " \
            "\n      Also try --vv" % sys.argv[0]
    # Include default Omni command line options
    # Support unittest option by replacing -v and -q with --vv a --qq
    Test.unittest_parser(parser=parser, 
                         usage=usage)
    # Invoke unit tests as usual
    unittest.main()


