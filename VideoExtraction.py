import cv2
from imageai.Detection import ObjectDetection
from pathlib import Path
import shutil
import datetime

"""
Part of an ongoing "Smart Webcam" project.
Cuts out any parts of a video that does not have any humans visible.

In the same folder as this file create 3 sub-folders:
    -> humans   # Stores videos of detected humans
    -> frames   # Stores frames extracted from video
    -> models   # Stores pre-trained models. All should be set-up already, though
    -> temp     # Temporary folder for analysed images.
    
After running the code, please empty the frames and temp folder. This shall be automated in the future.
By 1llusion
"""


class VideoExtraction:
    iteration = 0
    total_duration = -1  # Total duration of videos in fps
    total_count = -1    # Total count of videos
    average_duration = -1   # Average length of videos in fps

    def __init__(self, modelPath="./models/yolo.h5"):
        self.detector = ObjectDetection()
        self.detector.setModelTypeAsYOLOv3()

        self.detector.setModelPath(modelPath)
        self.detector.loadModel()
        self.custom_detector = self.detector.CustomObjects(person=True,
                                        giraffe=True)  # Finding out if humans are in the image. And giraffes, because that would be hilarious.

    """
    Starts the extraction of frames and human recognition
    video = path to video file
    iteration = if called from a loop with multiple videos in a folder, enter the loop iteration here
    """
    def start(self, video, file_prefix=""):
        fps = self.extract(video)

        # If total duration was set, calculate the average duration.
        if self.total_duration >= 0:
            self.average_duration = self.total_duration / self.total_count
            # Preventing division by 0 error
            if fps <= 0:
                fps = 24
            average_seconds = (self.total_duration / self.total_count) / fps
            print("The average duration of a video is " + str(datetime.timedelta(seconds=average_seconds)))

        file_suffix = Path(video)
        file_suffix = file_suffix.suffix
        # Adding iteration to name so that a video does not get overwritten
        name = Path(file_prefix + "_" + str(self.iteration) + file_suffix)
        self.identifyHuman("frames", video, fps=fps, outputName=name)
        self.iteration += 1

    """
    Extracts frames from videos
    """
    def extract(self, video):
        vidcap = cv2.VideoCapture(video)
        fps = vidcap.get(cv2.CAP_PROP_FPS)

        success = True  # Frame read
        count = 0   # Number of frames read

        print("Started extracting " + video + "...")
        while success:
            # Reading and writing frame
            success, image = vidcap.read()
            if success:
                cv2.imwrite("frames/%d.jpg" % count, image)
            count += 1

        print("Video extracted!")
        # Return fps
        return fps
    """
    Detect all images with humans present and move them from inputFolder to outputFolder
    
    inputFolder = Folder where to search for images
    outputFolder = Where to store detected humans
    probability = What % of confidence should be used for detection?
    modelPath = Path to a pre-trained model
    
    Credit: https://stackabuse.com/object-detection-with-imageai-in-python/
    """
    def identifyHuman(self, inputFolder, inputVideo, outputFolder="humans", tempFolder="./temp/", fps=24, outputName="", probability=30):
        path = Path(inputFolder)   # To keep path structures tidy

        files = path.glob("**/*")

        count = 0   # Counting how many files were checked
        max_count = len(list(path.glob("**/*"))) - 3 * (self.average_duration / 4)    # Setting maximum count at video length at 1/4 of the video
        for file in [x for x in files if x.is_file()]:
            # Checking if we are near the last 2 seconds
            if count > max_count:
                break

            temp_file = Path(tempFolder + file.name)

            detections = self.detector.detectCustomObjectsFromImage(custom_objects=self.custom_detector,
                                                               input_image=file,
                                                               #output_type="array",
                                                               output_image_path=str(temp_file), # Keeping the same filename
                                                               minimum_percentage_probability=probability)
            # Was a human detected?
            if any(d['name'] == "person" for d in detections):
                print("Found humans! Copying file...")
                # Copying the video into the desired human folder
                shutil.copy(inputVideo, str(Path(outputFolder, str(outputName))))
                print("Finished copying file.")
                break   # Breaking out of the for loop

            count += 1

        # Cleanup (remove all files from frame and temp folders)
        print("Cleaning up...")
        for img in Path(inputFolder).glob("**/*"):
            img.unlink()

        for img in Path(tempFolder).glob("**/*"):
            img.unlink()

        print("Cleanup finished.")

    """
    Adds up the duration of videos and counts them (in fps)
    This is used to save time analysing videos
    """
    # Credit: https://stackoverflow.com/questions/49048111/how-to-get-the-duration-of-video-using-cv2
    def getTotalLength(self, video):
        cap = cv2.VideoCapture(video)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.total_duration += frame_count
        self.total_count += 1
        print("Current duration: " + str(self.total_duration))
"""
Example of how to run the class. Just enter a path of a video to be processed and go for a coffee.
"""
if __name__ == "__main__":
    vid = VideoExtraction()
    vid.start("Path to video to extract", "File Prefix")
    print("Done")