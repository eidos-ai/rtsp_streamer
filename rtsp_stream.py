#!/usr/bin/env python3
from threading import Thread

import cv2
import argparse
import gi
import time


gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject, GLib

class FrameLoader:
    def __init__(self, video_path):
        self.video_path = video_path
        self.stop = False
        self.last_frame = None

    def start(self):
    	# start the thread
        t = Thread(target=self.run, name="frameloader", args=())
        t.daemon = True
        t.start()
        return self

    def run(self):
        while not self.stop:
            cap = cv2.VideoCapture(self.video_path)
            while(cap.isOpened()):
                exist_frame, frame = cap.read()
                if exist_frame:
                    self.last_frame = frame
                    time.sleep(1 / 25)
                else:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def get_frame(self):
        return self.last_frame

    def get_size(self):
        cap = cv2.VideoCapture(self.video_path)
        width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height  = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return int(width), int(height)


class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, frame_loader, **properties):
        super(SensorFactory, self).__init__(**properties)
        self.number_frames = 0
        self.frame_loader = frame_loader
        self.fps = 30
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.width, self.height = frame_loader.get_size()
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96'.format(self.width, self.height, self.fps)

    def on_need_data(self, src, lenght):
        frame = self.frame_loader.get_frame()
        if frame is not None:
            data = frame.tostring()
            buf = Gst.Buffer.new_allocate(None, len(data), None)
            buf.fill(0, data)
            buf.duration = self.duration
            timestamp = self.number_frames * self.duration
            buf.pts = buf.dts = int(timestamp)
            buf.offset = timestamp
            self.number_frames += 1
            retval = src.emit('push-buffer', buf)
            if retval != Gst.FlowReturn.OK:
                print(retval)

    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)



if __name__ == '__main__':
    args = argparse.ArgumentParser()
    #create_indexes()
    args.add_argument("-v", "--video_path", required=True, help="path of the video to streap")
    args.add_argument("-p", "--port", required=False, default="8554", help="port to stream")

    args = vars(args.parse_args())
    video_path = args["video_path"]
    port = args["port"]


    mount_point = "/stream"

    GObject.threads_init()
    Gst.init(None)

    frame_loader = FrameLoader(video_path).start()
    server = GstRtspServer.RTSPServer.new()
    factory = SensorFactory(frame_loader)
    # factory.set_shared(True)

    server.set_service(port)
    mounts = server.get_mount_points()
    mounts.add_factory(mount_point, factory)
    server.attach()

    #  start serving
    print ("stream ready at rtsp://127.0.0.1:" + port + mount_point);

    loop = GLib.MainLoop()
    loop.run()
