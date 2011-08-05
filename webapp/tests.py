import unittest
from models import *
from utility_models import *
from rapidsms.tests.scripted import TestScript

class TestWebapp(TestScript):
    fixtures = ['observers', 'unknown_rcs']

    def setUp(self):
        super(TestWebapp, self).setUp()

    def Checklist(self):
        self.assertInteraction("""
          727336 > psc111111vr12rc999
          727336 < Observer ID not found. Please resend with valid PSC. You sent: PSC111111VR12RC999
    	  727336 > PSC366001VRRC113A2B1C2D4E5F2G2
    	  727336 < Invalid message:"PSC366001VRRC113A2B1C2D4E5F2G2". Please resend!
    	  727336 > PSC366001VR03RC113A2B3C2D4E5F2G3
    	  727336 < Invalid response(s) for question(s): "B, G". You sent: PSC366001VR03RC113A2B3C2D4E5F2G3
    	  727336 > PSC366001VR03RC11A2B1C2D4E5F2G2
    	  727336 < Invalid message:"PSC366001VR03RC11A2B1C2D4E5F2G2". Please resend!
    	  727336 > PSC712001VR22RC005A2B1C2D4E24FG2
    	  727336 < Invalid responses for the checklist code: "FG". You sent: PSC712001VR22RC005A2B1C2D4E24FG2
    	  727336 > PSC172001VR22GA639!5E
    	  727336 < Invalid message:"PSC172001VR22GA639!5E". Please resend!
    	  727336 > PSC172001VR22GA639!
    	  727336 < Invalid message:"PSC172001VR22GA639!". Please resend!
    	  727336 > PSC786001VR20RC157A3B1C2D4E5FN0NG2
    	  727336 < Invalid responses for the checklist code: "NG, FN". You sent: PSC786001VR20RC157A3B1C2D4E5FN0NG2
    	  727336 > PSC510001VR20RC137A1B1C2D4E234F0G1
    	  727336 < VR Checklist report accepted! You sent: PSC510001VR20RC137A1B1C2D4E234F0G1
    	  727336 > PSC510001VR20RC137A1B1C12D4E234F70G1
    	  727336 < Invalid response(s) for question(s): "C, F". You sent: PSC510001VR20RC137A1B1C12D4E234F70G1
    	  727336 > psc584001vr20rc103h1j1k2m1n5p4q5r5s1t2u2v2w2x2y4z420aa420
    	  727336 < VR Checklist report accepted! You sent: PSC584001VR20RC103H1J1K2M1N5P4Q5R5S1T2U2V2W2X2Y4Z420AA420
    	  727336 > psc319002vr20rc009ang/galadimaa1b1c31e2f9g3
    	  727336 < Invalid responses for the checklist code: "AD, MAA, ANGGA". Invalid response(s) for question(s): "C, G". You sent: PSC319002VR20RC009ANGGA1AD1MAA1B1C31E2F9G3
    	  727336 > PSC319002VR15RC139A1B1C3D45F8G12NDTEXTANGGA1AD1MA11A1B1C3D4E5F8G13RDTEXTGH1J1K2M5N5P5Q5R5S1T1U1V1W2X2Y999Z9999AA9999
    	  727336 < Invalid responses for the checklist code: "RDTEXTGH, NDTEXTANGGA, AD, MA". Invalid response(s) for question(s): "G". You sent: PSC319002VR15RC139A1B1C3D45F8G12NDTEXTANGGA1AD1MA11A1B1C3D4E5F8G13RDTEXTGH1J1K2M5N5P5Q5R5S1T1U1V1W2X2Y999Z9999AA9999
    	  727336 > psc844001vr15rc102h1j1m1n1p1q1r1s1tnovnoynonznonaanon
    	  727336 < Invalid responses for the checklist code: "TN, YN, NAAN, VN, NZN". You sent: PSC844001VR15RC102H1J1M1N1P1Q1R1S1TN0VN0YN0NZN0NAAN0N
    	  727336 > psc84001vr15rc269h1j1k1m1n5p5q5r5s1t2u2v1w2x2y8z8aa8@registration started late and very slow
    	  727336 < Invalid message:"PSC84001VR15RC269H1J1K1M1N5P5Q5R5S1T2U2V1W2X2Y8Z8AA8". Please resend!
	  """)

    def testIncident(self):
    	self.assertInteraction("""
    	  727336 > 1234VR25PSTN77!ABC
    	  727336 < Correct Incident
    	  727336 > 5678VR25PSTN77!ABC
    	  727336 < Observer ID not found. Please resend with valid Observer ID. You sent: 5678VR25PSTN77!ABC
    	  727336 > 7895VR25PSTN77!ABC
    	  727336 < Correct Incident
    	  727336 > 7895VR25PSTN77!ABC@I am off the ground
    	  727336 < Correct Incident
    	  727336 > 1234VR25PSTN7!ABC@I am off the ground
    	  727336 < Unknown location with code: 7
    	  727336 > 1234PR25PSTN77!ABC@I am off the ground
    	  727336 < Invalid message:"1234PR25PSTN77!ABC". Please resend!
    	  727336 > 1234VR25PSTN77!ABCZNP0@I am off the ground
    	  727336 < Unknown critical incident code: "0, N, P, Z"
    	  727336 > 7895VR25z77!ABC
    	  727336 < Invalid message:"7895VR25Z77!ABC". Please resend!
	  """)

