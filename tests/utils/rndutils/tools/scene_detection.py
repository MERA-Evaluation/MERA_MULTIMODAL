import glob
import os.path
import subprocess as sp

import pandas as pd
from scenedetect import AdaptiveDetector, SceneManager, open_video
from scenedetect.scene_manager import save_images
from scenedetect.video_splitter import split_video_ffmpeg

from rndutils.utils.logger import get_logger
from rndutils.utils.misc import find_dataset

logger = get_logger(__name__)


class SceneCutter:
    def __init__(self):
        self.__check_ffmpeg_installation()

    @staticmethod
    def __check_ffmpeg_installation():
        result = sp.getstatusoutput("ffmpeg --help")
        if result[0] != 0:
            raise Exception("ffmpeg library not installed, please install")
        else:
            logger.info("ffmpeg installed")

    def __get_files_to_process(self, folder: str):
        return glob.glob(f"{folder}/*")

    def __validate_ffmpeg_installation(self):
        result = sp.getstatusoutput("ffmpeg --help")
        if result[0] != 0:
            raise Exception("ffmpeg library not installed, please install")
        else:
            pass

    def __filter_scenes_by_duration(
        self,
        scenes: list,
        fps: float,
        filename: str,
        minimum_duration_sec: int = 5,
        maximum_duration_sec: int = 60,
    ):
        filtered_scenes = []
        scene_stats = []
        for i, scene in enumerate(scenes):
            start_scene_timecode = scene[0].get_timecode()
            end_scene_timecode = scene[1].get_timecode()
            start_scene_frame = scene[0].get_frames()
            end_scene_frame = scene[1].get_frames()
            diff = end_scene_frame - start_scene_frame
            scene_duration_sec = diff / int(fps)
            good_scene = (
                False
                if scene_duration_sec < minimum_duration_sec
                or scene_duration_sec > maximum_duration_sec
                else True
            )
            scene_stats.append(
                (
                    i + 1,
                    start_scene_timecode,
                    end_scene_timecode,
                    start_scene_frame,
                    end_scene_frame,
                    fps,
                    scene_duration_sec,
                    diff,
                )
            )
            if good_scene:
                filtered_scenes.append(scene)
        self.__save_scene_stats(scene_stats=scene_stats, filename=filename)
        self.scene_stats = scene_stats
        logger.info(
            f"Scenes before filtration: {len(scenes)}, after filtration: {len(filtered_scenes)}"
        )
        return filtered_scenes

    @staticmethod
    def __init_scene_manager():
        scene_manager = SceneManager()
        scene_manager.add_detector(AdaptiveDetector())
        return scene_manager

    @staticmethod
    def __split_video_to_scenes(
        video_path: str, scenes: list, target_folder: str, file_extension: str
    ):
        total_cnt = len(scenes)
        target_file_template = (
            f"{target_folder}/$VIDEO_NAME-Scene-$SCENE_NUMBER-{total_cnt}.mp4"
        )
        os.makedirs(target_folder, exist_ok=True)
        split_video_ffmpeg(
            input_video_path=video_path,
            scene_list=scenes,
            output_file_template=target_file_template,
            show_progress=True,
        )

    def __save_scene_stats(self, scene_stats: list, filename: str):
        stat_filename = f"{filename.split('.')[0]}.csv"
        stats = pd.DataFrame(
            data=scene_stats,
            columns=[
                "scene_num",
                "scene_timecode_start",
                "scene_timecode_end",
                "scene_frame_start",
                "scene_frame_end",
                "fps",
                "scene_duration_sec",
                "scene_duration_frames",
            ],
        )
        logger.info(f"Save stats to file {stat_filename}")
        stats.to_csv(stat_filename, sep=",", index=False)

    def process(
        self,
        source_folder: str,
        base_target_folder: str,
        exception_list: list = None,
        minimum_duration_sec: int = 5,
        maximum_duration_sec: int = 60,
        get_screenshots: bool = False,
        target_screenshots_folder: str = None,
        num_screenshot_images: int = 1,
        frame_margin: int = 1,
        get_scenes: bool = True,
    ):
        """
        Method to detect and save scenes and their screenshots of provided videos.

        Args:
            source_folder (str): Input directory with videos.
            base_target_folder (str, optional): Output directory for scene videos.
                Must be provided if get_scenes=True. Defaults to None.
            exception_list (list, optional): List of exception files.
            minimum_duration_sec (int, optional): Minimum scene duration in seconds
                to be created as a separate video. Defaults to 5.
            maximum_duration_sec (int, optional): Maximum scene duration in seconds
                to be created as a separate video. Defaults to 60.
            get_screenshots (bool, optional): If set to True, creates and saves
                a set number _num_screenshot_images_ of images from each scene.
                Defaults to False.
            target_screenshots_folder (str, optional): Output directory for scene screenshots.
                Must be provided if get_screenshots=True. Defaults to None.
            num_screenshot_images (int, optional): Number of images to generate per scene.
                Will always include start/end frame, unless -n=1, in which case
                the image will be the frame at the mid-point of the scene.
                Minimum is 1. Defaults to 1.
            frame_margin (int, optional): Number of frames
                to pad each scene around the beginning and end
                (e.g. moves the first/last image into the scene by N frames).
                Can set to 0, but will result in some video files failing to extract
                the very last frame. Minimum is 0. Defaults to 1.
            get_scenes (bool, optional): If set to True, creates and saves
                detected scenes. Defaults to True.

        Raises:
            TypeError: if get_screenshots is set to True, but target_screenshots_folder is not provided.
            TypeError: if get_scenes is set to True, but target_folder is not provided.
        """
        files_to_process = find_dataset(source_folder, skip_formats=".DS_Store")
        for video_path in files_to_process:
            filename = os.path.basename(video_path)
            file_name, file_extension = os.path.splitext(video_path)
            # replace for save the hierarchy
            target_folder = os.path.dirname(video_path).replace(
                source_folder, base_target_folder
            )
            if exception_list and file_name in exception_list:
                logger.info(f"Skipped {video_path}")
                continue
            try:
                video = open_video(path=video_path)
            except Exception:
                continue
            logger.info(f"File extension: {file_extension} ({video_path})")
            scene_manager = self.__init_scene_manager()
            scene_manager.detect_scenes(video=video, show_progress=True)
            scenes = scene_manager.get_scene_list()
            filtered_scenes = self.__filter_scenes_by_duration(
                scenes=scenes,
                fps=video.frame_rate,
                minimum_duration_sec=minimum_duration_sec,
                maximum_duration_sec=maximum_duration_sec,
                filename=filename,
            )
            if get_screenshots:
                if target_screenshots_folder is None:
                    print_error = "Missing argument: "
                    print_error += "get_screenshots is set to True, but target_screenshots_folder is not provided."
                    raise TypeError(print_error)
                os.makedirs(target_screenshots_folder, exist_ok=True)
                save_images(
                    filtered_scenes,
                    video,
                    num_images=num_screenshot_images,
                    frame_margin=frame_margin,
                    output_dir=target_screenshots_folder,
                    image_extension="jpg",
                    show_progress=True,
                )
            del video
            if get_scenes:
                if target_folder is None:
                    raise TypeError(
                        "Missing argument: get_scenes is set to True, but target_folder is not provided."
                    )
                self.__split_video_to_scenes(
                    video_path=video_path,
                    scenes=filtered_scenes,
                    target_folder=target_folder,
                    file_extension=file_extension,
                )


if __name__ == "__main__":
    scene_cutter = SceneCutter()
    scene_cutter.process(source_folder="source_videos", base_target_folder="cut_result")
