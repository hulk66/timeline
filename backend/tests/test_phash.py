import unittest
import imagehash
from PIL import Image


class TestpHash(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple_phash(self):

        hash = imagehash.phash(Image.open("tests/angie1.png"))
        assert hash is not None

        