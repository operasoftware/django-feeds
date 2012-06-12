import unittest2 as unittest

from djangofeeds import optimization

IMG1 = "http://feeds.feedburner.com/~r/Wulffmorgenthaler/~4/aFiizovyBmA"
IMG2 = IMG1 + ":qUKuBzXJMEQ:V_sGLiPBpWU"
IMG3 = "http://a.rfihub.com/eus.gif?eui=2224"

SERVICE_URLS = [IMG3, IMG1]

IMG_LIMIT = optimization.DJANGOFEEDS_SMALL_IMAGE_LIMIT


class test_BeaconRemover(unittest.TestCase):

    def setUp(self):
        self.tracker_remover = optimization.PostContentOptimizer()

    def test_01_urls(self):
        self.assertIsBeacons(SERVICE_URLS + [IMG2])

    def test_strip_tracker(self):
        some_text = """test %s %s"""
        to_img_tag = """<img src="%s" />"""
        img1 = to_img_tag % IMG2
        img2 = to_img_tag % "http://feeds.feedburner.com/"

        content = some_text % (img1, img2)
        expected_result = some_text % ("", img2)

        self.assertEqual(self.tracker_remover.optimize(content),
            expected_result)

    def test_no_optimization(self):
        self.assertEqual(self.tracker_remover.optimize(" test "), "test")

    def test_parse_borken_html(self):
        broken_html = """<a< <img src="test">"""
        self.assertEqual(self.tracker_remover.optimize(broken_html),
            """<a>&lt; <img src="test" /></a>""")

    def test_remove_extra_br(self):
        extra = """  <br /><br><br><br/> <a href="test">toto</a>
        <br><br><br>"""
        ecpected_result = """<a href="test">toto</a>\n<br />"""
        self.assertEqual(self.tracker_remover.optimize(extra),
                         ecpected_result)

    def test_remove_small_image(self):
        small_image = """<img src="test" width="%d">""" % (IMG_LIMIT - 1)
        self.assertEqual(
            self.tracker_remover.optimize(small_image),
            "")

    def test_big_enough_image(self):
        big_enough_image = """<img src="test" width="%d">""" % IMG_LIMIT
        self.assertEqual(
            self.tracker_remover.optimize(big_enough_image),
            '<img src="test" width="%d" />' % IMG_LIMIT)

    def test_remove_tracker(self):
        tracker_src = [
            'http://telegraph.feedsportal.com/c/test',
            'http://rss.feedsportal.com/c/32495/f/479227/s/20113027/mf.gif',
            'http://feeds.newscientist.com/c/749/f/10901/s/1fee0bac/mf.gif'
            'http://ads.pheedo.com/random',
            'http://a.rfihub.com/random',
            'http://segment-pixel.invitemedia.com/random',
        ]
        for src in tracker_src:
            tracker = """<img src="%s" width="%d">""" % (src, IMG_LIMIT + 1)
            self.assertEqual(self.tracker_remover.optimize(tracker), '')

    def test_settings(self):
        prev = optimization.DJANGOFEEDS_REMOVE_TRACKERS
        optimization.DJANGOFEEDS_REMOVE_TRACKERS = False
        try:
            to_img_tag = """<img src="%s" />"""

            for url in SERVICE_URLS:
                self.assertEqual(
                    self.tracker_remover.optimize(to_img_tag % url),
                    to_img_tag % url)
        finally:
            optimization.DJANGOFEEDS_REMOVE_TRACKERS = prev

    def assertIsBeacon(self, url):
        self.assertTrue(self.tracker_remover.looks_like_tracker(url))

    def assertIsBeacons(self, urls):
        map(self.assertIsBeacon, urls)
