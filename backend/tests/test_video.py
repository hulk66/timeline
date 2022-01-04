import unittest
import ffmpeg
from PIL import Image
import exiftool
import os

class Test_VideoConversion(unittest.TestCase):

    def test_mov_conversion(self) -> None:
        ffmpeg.input("tests/fjord.mov").output("tests/fjord.mp4",
                                             c="copy", movflags="faststart").overwrite_output().run()
        probe = ffmpeg.probe("tests/fjord.mp4")
        video_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        assert video_stream is not None
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        num_frames = int(video_stream['nb_frames'])
        assert width > 0
        assert height > 0
        assert num_frames > 0
        os.remove("tests/fjord.mp4")

    def test_thumbnail_creation(self) -> None:
        ffmpeg.input("tests/fjord.mov").filter("scale", 400, -2).output("tests/fjord_thumb.jpg", map_metadata=0, movflags="use_metadata_tags", vframes=1).overwrite_output().run()
        image = Image.open("tests/fjord_thumb.jpg")
        assert image.width == 400
        os.remove("tests/fjord_thumb.jpg")


    def test_preview_creation(self) -> None:
        # ffmpeg -i uhd.mov -vf scale=400:-2,setsar=1 -t 5 -pix_fmt yuv420p  -an -movflags faststart u1.mp4
        ffmpeg.input("tests/fjord.mov").filter("scale", 400, -2).output("tests/fjord_preview.mp4", map_metadata=0,
                                                                      movflags="+faststart +use_metadata_tags", 
                                                                      pix_fmt="yuv420p", t=5).overwrite_output().global_args("-an").run()
        # .filter("setsar", 1) \
        # .filter("pix_fmt", "yuv420p") \
        # .filter("t", 5) \
        # .filter("an") \
        probe = ffmpeg.probe("tests/fjord_preview.mp4")
        video_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        assert video_stream is not None
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        assert width == 400
        assert height < width
        os.remove("tests/fjord_preview.mp4")

    def test_gps_extraction(self):
        et = exiftool.ExifTool()
        assert et is not None
        et.start()
        assert et.get_metadata("tests/fjord.mov") is not None
        assert et.get_tag("Composite:GPSPosition", "tests/fjord.mov") == '60.9425 6.9264'
        assert et.get_tag("Composite:GPSPosition", "tests/tunnel.mp4") == '61.4222 7.0957'
        et.terminate()


