"""Snapshot drift check: sub-pixel transition jitter is no layout change, a real shift still is."""
import unittest

from tools.capture_packet import layout_key
from tools.review_io import digest


def index(y, h=33.3):
    return {'document_height': 14385, 'blocks': [{'text': 'Wie benutze ich Milvo Pro?', 'rect': {'y': y, 'h': h},
                                                  'tokens': [{'rects': [{'y': y, 'h': h}]}]}]}


class LayoutKeyTests(unittest.TestCase):
    def test_subpixel_jitter_is_stable(self):
        # SE 265: the FAQ icon rotating to × moved rects by 0.00002 px and failed every capture attempt.
        self.assertEqual(digest(layout_key(index(2803.3544311523438, 33.31134033203125))),
                         digest(layout_key(index(2803.3544158935547, 33.31135559082031))))

    def test_real_shift_is_a_change(self):
        self.assertNotEqual(digest(layout_key(index(2803.35))), digest(layout_key(index(2804.35))))

    def test_text_change_is_a_change(self):
        changed = index(2803.35); changed['blocks'][0]['text'] = 'Anders'
        self.assertNotEqual(digest(layout_key(index(2803.35))), digest(layout_key(changed)))


if __name__ == '__main__':
    unittest.main()
