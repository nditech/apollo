import unittest
from rapidsms.tests.scripted import TestScript

class TestPSC(TestScript):
    fixtures = ['observers', 'unknown_rcs']

    def setUp(self):
        super(TestPSC, self).setUp()

    def testVRChecklist(self):
        self.assertInteraction("""
          1234 > psc111111vr12rc999
          1234 < Observer ID not found. Please resend with valid PSC. You sent: PSC111111VR12RC999
        """)

    def testVRIncident(self):
    	pass

    def testDCOChecklist(self):
	    pass

    def testDCOIncident(self):
	    pass
