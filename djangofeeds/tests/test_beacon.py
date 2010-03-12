import unittest2 as unittest

from djangofeeds import optimization

IMG1 = "http://feeds.feedburner.com/~r/Wulffmorgenthaler/~4/aFiizovyBmA"
IMG2 = IMG1 + ":qUKuBzXJMEQ:V_sGLiPBpWU"
IMG3 = "http://a.rfihub.com/eus.gif?eui=2224"

SERVICE_URLS = [IMG3, IMG1]


class test_BeaconRemover(unittest.TestCase):

    def setUp(self):
        self.beacon_remover = optimization.BeaconRemover()

    def test_01_urls(self):
        self.assertIsBeacons(SERVICE_URLS + [IMG2])

    def test_02_strip(self):
        some_text = """test %s %s"""
        to_img_tag = """<img src="%s" />"""
        img1 = to_img_tag % IMG2
        img2 = to_img_tag % "http://feeds.feedburner.com/"

        content = some_text % (img1, img2)
        expected_result = some_text % ("", img2)

        self.assertEqual(self.beacon_remover.strip(content), expected_result)

    def test_no_img_optimization(self):
        self.assertEqual(self.beacon_remover.strip(" test "), " test ")

    def test_parse_error(self):
        unparseable_text = """<a< <img>"""
        self.assertEqual(self.beacon_remover.strip(unparseable_text),
                         unparseable_text)

    def test_special_condition(self):
        condition = """<img src="">"""
        # FIXME shouldn't it assert something?
        self.beacon_remover.strip(condition)

    def test_03_settings(self):
        prev = optimization.DJANGOFEEDS_REMOVE_BEACON
        optimization.DJANGOFEEDS_REMOVE_BEACON = False
        try:
            to_img_tag = """<img src="%s" />"""

            for url in SERVICE_URLS:
                self.assertEqual(self.beacon_remover.strip(to_img_tag % url),
                                 to_img_tag % url)
        finally:
            optimization.DJANGOFEEDS_REMOVE_BEACON = prev

    def assertIsBeacon(self, url):
        self.assertTrue(self.beacon_remover.looks_like_beacon(url))

    def assertIsBeacons(self, urls):
        print("URLS: %s" % urls)
        map(self.assertIsBeacon, urls)
