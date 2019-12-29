from pathlib import Path
from VideoExtraction import VideoExtraction


class FileFeeder:
    extension = "*"
    """
    Add a default extension to look for.
    Can work as a wildcard if nothing is passed or * is passed.
    """
    def __init__(self, extension="*"):
        if extension is not "*":
            # An extension with a dot is passed: .avi
            if extension[0] is ".":
                self.extension = "*" + extension
            # A single file was passed: video.avi
            elif "." in extension:
                self.extension = extension
            # Just the extension was passed: avi
            else:
                self.extension = "*." + extension

    """
    Starts processing all the found files
    """
    def start(self, basePath="."):
        extractor = VideoExtraction()
        base = Path(basePath)

        print("Getting average duration of videos...")
        for file in base.glob("**/" + self.extension):
            extractor.getTotalLength(str(file))
        print("Average duration calculated!")

        print("Starting extraction")
        for file in base.glob("**/" + self.extension):
            # Extracting the date sub-folder
            file_prefix = file.relative_to(base)
            extractor.start(str(file), str(file_prefix.parent.parent))
        print("Finished")


if __name__ == "__main__":
    feeder = FileFeeder(".avi")
    feeder.start("Path to videos folder")