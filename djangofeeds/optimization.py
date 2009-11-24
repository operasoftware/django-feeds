from httplib2 import Http
from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParseError

BEACON_REQUEST_METHOD = "HEAD"
BEACON_MIN_IMAGE_SIZE = 100
BEACON_VERIFY_ZERO_BYTES = True


class BeaconDetector(object):
    min_image_size = BEACON_MIN_IMAGE_SIZE
    verify_zero_bytes = BEACON_VERIFY_ZERO_BYTES
    request_method = BEACON_REQUEST_METHOD

    def __init__(self, min_image_size=None, verify_zero_bytes=None,
            request_method=None):
        self.min_img_size = min_image_size or self.min_image_size
        self.verify_zero_bytes = verify_zero_bytes or self.verify_zero_bytes
        self.request_method = request_method or self.request_method
        self._http = Http()

    def _get_image_size(self, image_url, request_method):
        resp, content = self._http.request(image_url, request_method)
        return int(resp.get("content-length", 0)) or len(content)

    def looks_like_beacon(self, image_url, verify=None):
        verify = verify or self.verify_zero_bytes
        request_method = "GET" if verify else self.request_method
        try:
            image_size = self._get_image_size(image_url, request_method)
        except TypeError:
            return True
        if not image_size:
            if not verify and self.verify_zero_bytes:
                return self.looks_like_beacon(image_url, verify=True)
            return True
        if image_size < self.min_image_size:
            return True
        return False

    def stripsafe(self, text):
        if "<img" not in text:
            return text
        try:
            return self.strip(text)
        except HTMLParseError:
            return text

    def strip(self, html):
        soup = BeautifulSoup(html)
        stripped_count = 0
        for image in soup("img"):
            image_source = image.get("src")
            if image_source and "://" in image_source:
                if self.looks_like_beacon(image_source):
                    image.replaceWith("")
                    stripped_count += 1
        return str(soup) if stripped_count else html
