import subprocess
import os
import json
import datetime
import pathlib
import tarfile
import boto3

RUN_DT = int(datetime.datetime.utcnow().timestamp())
EXPORT_PARENT_FOLDER = f"/config/backup/backup-{RUN_DT}"
pathlib.Path(EXPORT_PARENT_FOLDER).mkdir(parents=True, exist_ok=True)

backup_root_folder = pathlib.Path(EXPORT_PARENT_FOLDER).parent
pathlib.Path(f"{backup_root_folder}/latest").unlink(missing_ok=True)
latest = pathlib.Path(f"{backup_root_folder}/latest")
latest.symlink_to(EXPORT_PARENT_FOLDER)


def RunThis(cmd: list):
    cmd = " ".join(cmd)
    p = subprocess.Popen(cmd, shell=True)
    p.wait()


class BaseJob:
    def __init__(self):
        self._NAME = ""
        self._JOBTYPE = ""
        self._data = dict()

    def Load(self, data: dict):
        self._data = data
        if "credentials" in self._data and isinstance(self._data.get("credentials", {}), dict):
            for key, value in self._data.get("credentials", {}).items():
                if value[0:4] == "env:":
                    self._data["credentials"][key] = os.environ.get(value[4:], "VALUE_NOT_FOUND_IN_ENVIRONMENT")

    def LoadJson(self, data: str):
        self._data = json.loads(data)
        if "credentials" in self._data and isinstance(self._data.get("credentials", {}), dict):
            for key, value in self._data.get("credentials", {}).items():
                if value[0:4] == "env:":
                    self._data["credentials"][key] = os.environ.get(value[4:], "VALUE_NOT_FOUND_IN_ENVIRONMENT")

    def Run(self):
        pass


class DumpMySqlDatabaseJob(BaseJob):
    def __init__(self):
        super().__init__()
        self._NAME = "DumpMySqlDatabase"
        self._JOBTYPE = "{}_Job".format(self._NAME)

    def Run(self):

        output_dir = "{}/{}".format(EXPORT_PARENT_FOLDER, self._data['job_name'])
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = "{}/{}.sql".format(output_dir, self._data["job_name"])

        print("Database Export Job: [{Job_Name}] starting at {dt}".format(Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

        cmd = [
                "mysqldump", 
                "--all-databases", 
                "--user={}".format(self._data['credentials']['username']), 
                "--password={}".format(self._data['credentials']['password']), 
                "--host={}".format(self._data['host']),
                "--port={}".format(self._data['port']),
                "--result-file={}".format(output_file),
                "--ignore-table=mysql.general_log",
                "--ignore-table=mysql.slow_log",
                "--ignore-table=mysql.user",
                "--skip-lock-tables"
        ]

        RunThis(cmd)
        
        print("Database Export Job: [{Job_Name}] done at {dt}".format(Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

class DumpMySqlSingleDatabaseJob(BaseJob):
    def __init__(self):
        super().__init__()
        self._NAME = "DumpMySqlSingleDatabase"
        self._JOBTYPE = "{}_Job".format(self._NAME)

    def Run(self):

        output_dir = "{}/{}".format(EXPORT_PARENT_FOLDER, self._data['job_name'])
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = "{}/{}.sql".format(output_dir, self._data["job_name"])

        print("Database Export Job: [{Job_Name}] starting at {dt}".format(Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

        cmd = [
                "mysqldump", 
                "--databases {}".format(self._data['database']), 
                "--user={}".format(self._data['credentials']['username']), 
                "--password={}".format(self._data['credentials']['password']), 
                "--host={}".format(self._data['host']),
                "--port={}".format(self._data['port']),
                "--result-file={}".format(output_file),
                "--ignore-table=mysql.general_log",
                "--ignore-table=mysql.slow_log",
                "--ignore-table=mysql.user",
                "--skip-lock-tables"
        ]

        RunThis(cmd)
        
        print("Database Export Job: [{Job_Name}] done at {dt}".format(Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


class DumpPostgresDatabaseJob(BaseJob):
    def __init__(self):
        super().__init__()
        self._NAME = "DumpPostgresDatabase"
        self._JOBTYPE = "{}_Job".format(self._NAME)

    def Run(self):

        output_dir = "{}/{}".format(EXPORT_PARENT_FOLDER,
                                    self._data['job_name'])
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = "{}/{}.sql".format(output_dir, self._data["job_name"])

        print("Database Export Job: [{Job_Name}] starting at {dt}".format(
            Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

        cmd = [
            "pg_dumpall",
            "--file={}".format(output_file),
            "--no-password",
            "--dbname=postgresql://{user}:{secret}@{host}:{port}".format(
                user=self._data['credentials']['username'], secret=self._data['credentials']['password'], host=self._data['host'], port=self._data['port']),
        ]

        RunThis(cmd)

        print("Database Export Job: [{Job_Name}] done at {dt}".format(
            Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


class DirectoryBackupJob(BaseJob):
    def __init__(self):
        super().__init__()
        self._NAME = "DirectoryBackup"
        self._JOBTYPE = "{}_Job".format(self._NAME)

    def Run(self):

        output_dir = "{}/{}".format(EXPORT_PARENT_FOLDER,
                                    self._data['job_name'])
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = "{}/{}.tar.gz".format(output_dir, self._data["job_name"])

        tmp_input_dir = "{}/{}_tmp".format(EXPORT_PARENT_FOLDER,
                                           self._data['job_name'])
        pathlib.Path(tmp_input_dir).mkdir(parents=True, exist_ok=True)

        print("Directory Backup Job: [{Job_Name}] starting at {dt}".format(
            Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

        cmd = [
            "cp",
            "-R",
            "{}/*".format(self._data['path']),
            tmp_input_dir
        ]

        RunThis(cmd)

        with tarfile.open(output_file, "w:gz") as tgz:
            if len(self._data["path_archive_name"]) == 0:
                tgz.add(tmp_input_dir)
            else:
                tgz.add(tmp_input_dir, arcname=self._data['path_archive_name'])

        cmd = ["chmod", "-R", "777", tmp_input_dir]
        RunThis(cmd)

        cmd = ["rm", "-rf", tmp_input_dir]
        RunThis(cmd)

        print("Directory Backup Job: [{Job_Name}] done at {dt}".format(
            Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


class S3UploadJob(BaseJob):
    def __init__(self):
        super().__init__()
        self._NAME = "S3Upload"
        self._JOBTYPE = "{}_Job".format(self._NAME)

    def Run(self):
        print("S3 Upload Job: [{Job_Name}] starting at {dt}".format(
            Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

        client = boto3.client(
            's3',
            aws_access_key_id=self._data["credentials"]["aws_access_key"],
            aws_secret_access_key=self._data["credentials"]["aws_secret_access_key"]
        )

        output_file_name = "{}-{}.tar.gz".format(
            self._data["job_name"], RUN_DT)
        output_path = "/tmp/{}".format(output_file_name)

        with tarfile.open(output_path, "w:gz") as tgz:

            upload_path = self._data['path_for_upload']

            if pathlib.Path(upload_path).is_symlink():
                upload_path = pathlib.Path(upload_path).resolve(strict=True)

            tgz.add(str(upload_path), arcname=self._data['job_name'])

        client.upload_file(output_path, self._data['bucket_name'], output_file_name, ExtraArgs={
            "StorageClass": "STANDARD_IA"
        })

        cmd = ["rm", "-r", output_path]
        RunThis(cmd)

        print("S3 Upload Job: [{Job_Name}] done at {dt}".format(
            Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


class NotifyJob(BaseJob):
    pass


class S3SyncJob(BaseJob):
    def __init__(self):
        super().__init__()
        self._NAME = "S3Sync"
        self._JOBTYPE = "{}_Job".format(self._NAME)

    def Run(self):
        print("S3 Sync Job: [{Job_Name}] starting at {dt}".format(
            Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

        cmd = [
            "s3cmd",
            "--access_key={}".format(self._data['credentials']
                                     ['aws_access_key']),
            "--secret_key={}".format(self._data['credentials']
                                     ['aws_secret_access_key']),
            "--recursive",
            "--delete-removed",
            "--storage-class=STANDARD_IA",
            "--server-side-encryption",
            "sync",
            "{}".format(self._data['path']),
            "s3://{bucket}/{prefix}".format(
                bucket=self._data['bucket_name'], prefix=self._data['bucket_path_prefix'])
        ]

        RunThis(cmd)

        print("S3 Sync Job: [{Job_Name}] done at {dt}".format(
            Job_Name=self._data['job_name'], dt=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


def main():
    # Get Environment Variables
    JOB_FILE = "/config/jobs.json"
    if "JOB_FILE" in os.environ:
        JOB_FILE = os.environ["JOB_FILE"]
    # Read Job information from Config File

    ExportJobs = []
    UploadJobs = []
    NotifyJobs = []

    with open(JOB_FILE, 'r') as fd:
        d = json.loads(fd.read())

        for job in d["Export_Jobs"]:
            if job["job_subtype"] == "mysql_export":
                tmp = DumpMySqlDatabaseJob()
            elif job['job_subtype'] == 'postgres_export':
                tmp = DumpPostgresDatabaseJob()
            elif job['job_subtype'] == "single_mysql_export":
                tmp = DumpMySqlSingleDatabaseJob()
            elif job["job_subtype"] == "directory_backup":
                tmp = DirectoryBackupJob()
            else:
                print("Incorrect Job Type found: {}. Skipping.".format(
                    job["job_subtype"]))
                continue

            tmp.Load(job)
            ExportJobs.append(tmp)

        for job in d["Upload_Jobs"]:
            if job["job_subtype"] == "S3_upload":
                tmp = S3UploadJob()
            elif job['job_subtype'] == "S3_sync":
                tmp = S3SyncJob()

            else:
                print("Incorrect Job Type found: {}. Skipping.".format(
                    job["job_subtype"]))
                continue

            tmp.Load(job)
            UploadJobs.append(tmp)

    # Create Parent Directory
    pathlib.Path(EXPORT_PARENT_FOLDER).mkdir(parents=True, exist_ok=True)

    # Run Jobs
    for job in ExportJobs:
        job.Run()

    for job in UploadJobs:
        job.Run()

    for job in NotifyJobs:
        job.Run()


if __name__ == '__main__':
    main()
