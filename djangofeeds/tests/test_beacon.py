import os
import unittest
from djangofeeds.optimization import BeaconRemover
from django.conf import settings

SERVICE_URLS = [
    'http://a.rfihub.com/eus.gif?eui=2224',
    'http://feeds.feedburner.com/~r/Wulffmorgenthaler/~4/aFiizovyBmA'
]

class TestBeacon(unittest.TestCase):

    def test_01_urls(self):
        br = BeaconRemover()

        for url in SERVICE_URLS:
            self.assertTrue(br.looks_like_beacon(url))

        urls = [
            'http://feeds.feedburner.com/~ff/Wulffmorgen\
thaler?i=aFiizovyBmA:qUKuBzXJMEQ:V_sGLiPBpWU'
        ]

        for url in urls:
            self.assertFalse(br.looks_like_beacon(url))

    def test_02_strip(self):
        
        br = BeaconRemover()
        text = '''test %s %s'''

        img = '<img src="%s" />'
        img1 = img % 'http://feeds.feedburner.com/~r/Wulffmorgenthaler/~4/aFiizovyBmA'
        img2 = img % 'http://feeds.feedburner.com/'

        content = text % (img1, img2)
        expected_result = text % ('', img2)

        self.assertEqual(br.strip(content), expected_result)

        # test the no img optimization
        self.assertEqual(br.strip(' test '), ' test ')

        # generate a parse error
        parse_error = '<a< <img>'
        self.assertEqual(br.strip(parse_error), parse_error)

        # special codition
        condition = '<img src="">'
        br.strip(condition)

        

    def test_03_settings(self):

        from djangofeeds import optimization
        setattr(optimization, 'DJANGOFEEDS_REMOVE_BEACON', False)
        img = '<img src="%s" />'

        br = BeaconRemover()
        for url in SERVICE_URLS:
            self.assertEqual(br.strip(img % url), img % url)

        setattr(optimization, 'DJANGOFEEDS_REMOVE_BEACON', True)