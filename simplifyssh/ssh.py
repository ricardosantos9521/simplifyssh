import subprocess
from .randomString import *
import os
from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path


class SSH:
    __hostname = None
    __username = None
    __password = None

    def __init__(self, hostname, username):
        self.__hostname = hostname
        self.__username = username

    def set_password(self, password):
        self.__password = password

    def already_logged_in(self):
        """
            Verify if user is already logged via authorized_keys
        """
        random_string = randomString(15)
        with subprocess.Popen((f"ssh -oConnectTimeout=12 -oPasswordAuthentication=No {self.__username}@{self.__hostname} echo {random_string}").split(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE) as sub_p:
            stdout, stderr = sub_p.communicate()
        stdout_string = stdout.decode("utf-8").strip("\n")
        stderr_string = stderr.decode("utf-8").strip("\n")
        if stderr_string != "":
            return 0
        elif (stderr == None or stderr_string == "") and stdout_string == random_string:
            return 2
        else:
            return 1


    def __execute_command(self, command):
        """
            Execute command on remote
        """
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            client.load_system_host_keys()
            client.connect(self.__hostname, username=self.__username, password=self.__password)

            _, stdout, stderr = client.exec_command(command)

            stdout_text = stdout.read().decode()
            stderr_text = stderr.read().decode()

            if stderr_text != "":
                print(f"\nerror: {stderr_text}")

            if stderr_text == "":
                return ("ok", stdout_text)

        finally:
            client.close()

        return ("error", stderr_text)


    def validate_password(self):
        """
            Validate password on remote
        """
        random_string = randomString(15)

        result, stdout = __execute_command(f"echo {random_string}")
        list_stdout = str(stdout).split("\n")
        if result == "ok" and list_stdout[0] == random_string:
            return True
        else:
            return False


    def create_ssh_folder_on_remote(self):
        """
            Create .ssh/temp folder on remote
        """ 
        result, stdout = __execute_command(f"mkdir -p ~/.ssh/temp")

        if result == "ok" and stdout == "":
            return True
        else:
            return False


    def __copy_file(self, file_path, remotefilepath):
        """
            Copy file from local to remote
        """
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            client.load_system_host_keys()
            client.connect(self.__hostname, username=self.__username, password=self.__password)

            sftp = client.open_sftp()
            sftp.put(file_path, remotefilepath)
            sftp.close()

            return True

        finally:
            client.close()

        return False

    def get_home_from_remote_linux(self):
        """
            Get $HOME from remote machine linux
        """
        result, stdout = __execute_command(f"echo $HOME")

        home_path_remote = str(stdout).split("\n")[0]

        return home_path_remote


    def copy_id_rsa_pub(self, id_rsa_path):
        """
            Copy the id_rsa.pub to the remote .ssh/temp folder
        """
        id_rsa_path_pub = id_rsa_path + ".pub"
        #only works with linux
        home_path_remote = get_home_from_remote_linux()
        id_rsa_path_pub_remote = home_path_remote + "/.ssh/temp/id_rsa.pub"


        result = __copy_file(id_rsa_path_pub, id_rsa_path_pub_remote)

        return result


    def build_authorized_keys(self):
        """
            Concatenate id_rsa.pub with the authorized_keys and delete .ssh/temp
        """
        result, std = __execute_command(f"cat ~/.ssh/temp/id_rsa.pub >> ~/.ssh/authorized_keys")

        if result == "ok":
            result, _ = __execute_command(f"rm -rf ~/.ssh/temp")
            if result == "ok":
                return True

        return False