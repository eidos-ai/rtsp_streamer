## Requirements: ##
- `sudo apt install python3 python3-gst-1.0 gstreamer1.0-plugins-base gir1.2-gst-rtsp-server-1.0`
- `sudo apt-get install libx264-dev`
- `sudo apt install ffmpeg`
- install [h.264-decoder](https://itsfoss.com/install-h-264-decoder-ubuntu/)

## Run: ##

`python rtsp_stream.py -v video.mp4`

To save the stream as a local video:

`ffmpeg -i rtsp://127.0.0.1:8554/stream -acodec copy -vcodec copy abc.mp4`
