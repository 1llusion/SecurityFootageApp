import datetime
from pathlib import Path
from ftplib import FTP
from pymongo import MongoClient
from VideoExtraction import VideoExtraction


class FileFeeder:
    extension = "*"
    """
    Extension:
        Add a default extension to look for.
        Can work as a wildcard if nothing is passed or * is passed.
        
    FTP:
        If using FTP, set ftp=True
        ftp_host = Host for FTP connection
        ftp_user = Username for FTP login
        ftp_password = Password for FTP logn
        fpt_dir = Default directory to be working from in FTP
    """
    def __init__(self, extension="*", mongo_user="", mongo_password="", mongo_url="", mongo_db="", ftp=False,ftp_host="", ftp_user="", ftp_password="", ftp_dir=""):
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

        if ftp:
            self.ftp = FTP(host=ftp_host,
                           user=ftp_user,
                           passwd=ftp_password)
            self.ftp.cwd(ftp_dir)
            self.ftp_dir = ftp_dir  # For reseting FTP folder location

            # Creating MongoDB connection
            client = MongoClient("mongodb://"+mongo_user+":"+mongo_password+"@"+mongo_url+"/"+mongo_db)
            self.db = client[mongo_db]

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
    """
    Checks if the Db file locations are up to date
    """
    def checkDbCache(self):
        print("Checking DB Cache...")
        # Finding highest entry (highest submitted date)
        expiration = self.db.last_update.find_one(sort=[("expiration", -1)])

        # Subtracting 1 day from current date. Be careful with timezones if not ran on local network
        expiration_limit = datetime.datetime.now() - datetime.timedelta(days=1)

        # Checking if expiration exists or expiration  1 day out of date
        if not expiration or expiration['expiration'] <= expiration_limit:
            self.checkFtpFiles(['recordings'])
            self.db.last_update.insert_one({'expiration': datetime.datetime.now()})
        print("DB Cache check finished.")

    """
    Work through all folders and check them against MongoDb
    
    This code follows closely the following structure:
        recordings ->
            folders named after dates ->
                folders with recordings (rec001 etc.) ->
                    actual recordings
    """

    def checkFtpFiles(self, files, dir=""):
        print("Checking for new files on FTP...")
        '''
        If we are in the root folder, we will have only files with extensions
        '''
        ftp = self.ftp
        dot = 0
        # Counting files with extensions
        for file in files:
            dot += file.count(".")
        # If number of files with extensions equals files in folder, we are at the end of the tree
        if dot >= len(files):
            # Adding full directory location to each file
            for file in files:
                self.checkDbFile(dir + file)
            return

        out = []
        for file in files:
            # If a file has an extension, it's not a folder
            if "." in file:
                continue
            # Moving into the next folder
            file = dir + file
            ftp.cwd(file)
            lst = ftp.nlst()
            # Moving up the folder tree
            ftp.cwd("..")
            for _ in range(dir.count("/")):
                ftp.cwd("..")

            out.append(self.checkFtpFiles(lst, dir=file + "/"))
        print("FTP file check finished.")

    def checkDbFile(self, file):
        print("Checking file presence in DB...")
        count = self.db.files.count_documents({'location': file})
        if count:
            print("File found.")
            return

        self.db.file.insert_one({'location': file,
                                 'processed': False,
                                 'deleted': False,
                                 'added': datetime.datetime.now()})
        print("File added to DB.")

if __name__ == "__main__":
    feeder = FileFeeder(extension="extension",
                        ftp=True,
                        ftp_dir="ftp dirrectory",
                        ftp_host="ftp host",
                        ftp_user="ftp user",
                        ftp_password="ftp password",
                        mongo_db="mongodb database",
                        mongo_user="mongodb user",
                        mongo_password="mongodb password",
                        mongo_url="mongodb host")

    feeder.checkDbCache()
    #feeder.start("Path to videos folder")
