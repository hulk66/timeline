import context


import os
import unittest
import ffmpeg
from PIL import Image
import exiftool
from timeline.tasks.crud_tasks import create_asset, create_preview
from timeline.app import create_app
from timeline.extensions import db
from timeline.domain import Asset, Status
import shutil

 
class Test_VideoConversion(unittest.TestCase):

    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.test")
        with self.app.app_context():
            status = Status()
            status.last_import_album_id = 1
            db.session.add(status)
            db.session.commit()


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

    def test_create_asset(self):
        with self.app.app_context():
            create_asset("tests/fjord.mov")
            video = Asset.query.first()        
            create_preview(video.id)
            assert os.path.exists("tests/400/high_res/tests/fjord.mov.jpg")
            assert os.path.exists("tests/400/low_res/tests/fjord.mov.jpg")
            assert os.path.exists("tests/video/full/tests/fjord.mov.mp4")
            assert os.path.exists("tests/video/preview/tests/fjord.mov.mp4")
            probe = ffmpeg.probe("tests/video/full/tests/fjord.mov.mp4")
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            assert video_stream is not None
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            num_frames = int(video_stream['nb_frames'])
            assert width == 3840
            assert height== 2160
            assert num_frames > 0

            probe = ffmpeg.probe("tests/video/preview/tests/fjord.mov.mp4")
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            assert video_stream is not None
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            assert height== 400
            
            image = Image.open("tests/400/high_res/tests/fjord.mov.jpg")
            assert image.height == 400

            #shutil.rmtree("tests/400")
            #shutil.rmtree("tests/video")


if __name__ == '__main__':
    unittest.main()
