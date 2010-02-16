import os
import unittest
from djangofeeds.optimization import BeaconRemover

class TestBeacon(unittest.TestCase):

    def test_urls(self):
        br = BeaconRemover()

        urls = [
            'http://a.rfihub.com/eus.gif?eui=2224',
            'http://feeds.feedburner.com/~r/Wulffmorgenthaler/~4/aFiizovyBmA'
        ]

        for url in urls:
            self.assertTrue(br.looks_like_beacon(url))

        urls = [
            'http://feeds.feedburner.com/~ff/Wulffmorgen\
thaler?i=aFiizovyBmA:qUKuBzXJMEQ:V_sGLiPBpWU'
        ]

        for url in urls:
            self.assertFalse(br.looks_like_beacon(url))

    def test_strip(self):
        
        br = BeaconRemover()
        text = '''test %s %s'''

        img = '<img src="%s" />'
        img1 = img % 'http://feeds.feedburner.com/~r/Wulffmorgenthaler/~4/aFiizovyBmA'
        img2 = img % 'http://feeds.feedburner.com/'

        content = text % (img1, img2)
        expected_result = text % ('', img2)

        self.assertEqual(br.strip(content), expected_result)

