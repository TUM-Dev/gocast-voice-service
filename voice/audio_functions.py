import os
import subprocess
from pathlib import Path


def ffmpeg_video_to_hls_audio(source: str, destination: str):
    """Create audio only .ts segments and .m3u8 playlist"""
    playlist = os.path.join(destination, Path(source).stem + '.m3u8')
    segment_filename = os.path.join(destination, 'segment%04d.ts')
    subprocess.Popen(['ffmpeg', '-y',
                      '-i', source,
                      '-c:a', 'aac',
                      '-f', 'hls',
                      '-hls_time', '8',
                      '-hls_playlist_type', 'vod',
                      '-hls_flags', 'independent_segments',
                      '-hls_segment_type', 'mpegts',
                      '-hls_segment_filename', segment_filename,
                      '-vn',
                      playlist])
