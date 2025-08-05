import glob
import os
import shutil

import tempfile

import flywheel

from radlib.fw.flywheel_clients import uwhealthaz_client
from radlib.fws.fws_utils import fws_expand_file_path, fws_translate_file_path, fws_in_docker, \
    fws_upload_file_to_flywheel, fws_get_mounted_path, fws_separate_flywheel_labels, fws_is_flywheel_path, \
    fws_download_file_from_flywheel


# TODO: 202506 csk expand this to more granular exceptions as needed!
class FWSFileSetException(Exception):
    pass

class FWSFileSet:
    """

    fileset_name: a unique name to label the fileset; this will become the mount point for the dockter container

    original_path: a single path that the fileset is initialized with, can be a local path, or a flywheel path,
    can contain *

    scratch_path: a file path to local storage, used for read/write/temp space if not a physical file path,
    will be mounted as "scratch" inside the docker container. creates in system temp space if not provided

    get_local_paths(): one or more filesystem paths where the real file data can be found, either a local path, a path
    in the scratch space in the case of a flywheel file path. translated to a mounted drive for a docker file.
    this ia an actual path that you can use to find a file

    get_output_paths(): paths where the files from get_local_paths() can be sent to. Can be a local path, a path translated
    to a mounted drive, or a flywheel file path

    """


    def __init__(self,
                 fileset_name: str,
                 original_path: str,
                 scratch_path:str=None,
                 force_load:bool=False):
        """
        Creates a new instance of a fileset, which forms a bridge between a local folder or flywheel acquisition and a
        docker mount

        Parameters
        ----------
        fileset_name: str
            A name for the fileset. This will be used to find the fileset, and also to mount to the docker container
        original_path: str
            The base path for the fileset. Can be a local filesystem path, a flywheel path, or (more coming soon)
        scratch_path: str, optional
            A path in local filesystem that flywheel data/temporary objects can be stored. If not provided, the fileset
            reserves temporary space for it's use
        force_load: boolean, default False
            If not True, the fileset is initialzed and can be looked at without pulling data from Flywheel.
            Flywheel data gets pulled and saved by get_local_paths()

        """
        self.fileset_name = fileset_name
        self.scratch_path = tempfile.mkdtemp() if scratch_path is None else scratch_path

        # env_common_path is None if not within a docker
        self.env_common_path = os.getenv(f'{self.fileset_name}_MOUNT_POINT')
        self.original_path = original_path
        self.original_paths = fws_expand_file_path(self.original_path)

        # find where local files would go
        self.get_local_paths(force_flywheel_path=True)

        if force_load:
            # download the files to local
            self.load_local_files()


    def get_common_path(self) -> str:
        """
        get the "parent" path of files in the is fileset. if in the docker, this is the same
        as the mount point

        Returns
        -------
        a string representation of a path, whether local or flywheel or (other)
        """
        # in docker, use file set name
        if fws_in_docker():
            return f'/{self.fileset_name}'
        # original path exists, use local
        elif os.path.exists(self.get_base_path()):
            return self.get_base_path()
        else:
            return self.scratch_path


    def get_base_path(self) -> str:
        """
        the "base path" is the parent of the "original path"
        Returns
        -------
         A str representation of the parent of the original path

        """
        return os.path.dirname(self.original_path)

    def get_mount_path(self) -> str:
        """
        The "mount path" is the equivalent of the "common path", but always locak, hence the get_local_paths

        Returns
        -------
        A string representation of a path that is usable as a docker mount point
        """
        # make sure things are defined if you call this early
        self.get_local_paths()
        return self.get_common_path()

    def get_mount_string(self) -> str:
        """
        the "mount string" is a string that would be usable as a -v option to docker.

        Returns
        -------
        A string representation of the mount point, in this case used to build a docker-compose.yaml file
        """
        # make sure things are defined if you call this early
        return f'{self.get_common_path()}{os.path.sep}{self.fileset_name}:/{self.fileset_name}'

    def get_flywheel_file_objects(self) -> list:
        """
        if this fileset describes a flywheel path, return the files that belong to that path
        If not, return an empty list

        Returns
        -------
        A list of flywheel File objects. May be emote.
        """
        objs = []
        if not fws_is_flywheel_path(self.original_path):
            # not a flywheel path, so there are no objects
            return objs

        # expand
        expanded_paths = fws_expand_file_path(self.original_path)

        # use the flywheel api resolve function to get at the files
        fw_client = uwhealthaz_client()
        for expanded_path in expanded_paths:
            objs.append(fw_client.resolve(expanded_path.replace("fw://", ""))['path'][-1])
        return objs


    def get_metadata(self, reload:bool=True) -> dict:
        """
        grabs the metadata info from the file objects: tags, dicom, etc.

        Parameters
        ----------
        reload: bool, default False
            A quirk of the flywheel api is that you have to run reload() to access the .info. Leaving
            this open in case it is a performance improvement if you only want non-info stuff (TBD)

        Returns
        -------
        A dict of the metadata from flywheel

        """
        metadata = {}
        if fws_is_flywheel_path(self.original_path):
            # if from flywheel, pull the tags, info, and classification metadata from the file objects
            for file in self.get_flywheel_file_objects():
                if reload:
                    file=file.reload()
                metadata[file.name] = {'tags': file.tags, 'classification': file.classification, 'info': file.info}

        return metadata


    def get_local_paths(self, force_flywheel_path = False) -> list[str]:
        """
        A list of the "working" file paths on the local storage that the active machine is using.
        The first time this is called, flywheel info is downloaded to scratch space and these local
        paths will reflect that accessible data.

        Returns
        -------
        A list of file paths in the local filesystem that are accessible by the running code

        """
        # expand the wildcard(s)
        expanded_file_paths = fws_expand_file_path(self.original_path)

        self.local_paths = []
        for file_path in expanded_file_paths:
            if fws_in_docker():
                if os.path.exists(f'/{self.fileset_name}') and not os.path.isdir(f'/{self.fileset_name}'):
                    # single file
                    file_path = f'/{self.fileset_name}'

                else:
                    # folder
                    file_path = file_path.replace(self.env_common_path, f'/{self.fileset_name}')

            if fws_is_flywheel_path(self.original_path) or force_flywheel_path:
                # translate from flywheel path to local path
                self.local_paths.append(fws_translate_file_path(file_path, self.scratch_path, self))

            elif os.path.exists(file_path):
                # file exists, so this is a "direct" path
                self.local_paths.append(file_path)

            else:
                # raise an error
                raise FWSFileSetException(f"error when expanding {file_path} to a valid file!")

        return self.local_paths

    def load_local_files(self):
        # 2025-07 csk could be dedicated scratch space, don't download if it already exists!
        fw_client = uwhealthaz_client()

        for original_path, local_path in zip(self.original_paths, self.local_paths):
            try:
                returned_path = fws_download_file_from_flywheel(fw_client, original_path, local_path)
                if returned_path != local_path:
                    print("returned_path != local_path!")

            except flywheel.rest.ApiException as e:
                # if this is an output file in flywheel, it has not been created yet, but the rest of the goo needs to be done!
                print("exception ", e)
                return local_path

    def get_output_paths(self) -> list[str]:
        """
        The "opposite" of get_local_paths, this would be the (expanded) accessible file paths or flywheel
        paths that the elements of this fileset can be copied to after processing

        Returns
        -------
        A list of file paths in the local filesystem or flywheel that this fileset can be copied back to

        """
        # same as self.original_path, but expanded
        output_path = self.original_path

        if fws_in_docker():
            output_path = output_path.replace(self.get_common_path(), f'/{self.fileset_name}')

        if not output_path.endswith(os.path.sep):
            output_path = os.path.dirname(output_path)

        # TODO: 202507 csk using os.path.sep does not work in this case, someday I will figure out why
        sep = '/' if '\\' not in output_path else '\\'
        file_names = [f'{output_path}{sep}{os.path.basename(file_path)}' for file_path in self.get_local_paths()]

        return file_names


    def save_files(self):
        """
        Saves off the elements of this fileset to the results of get_output_paths, whether local or mounted or flywheel

        """
        fw_client = uwhealthaz_client()
        output_paths = []
        print("save_files!")
        if len(self.get_local_paths()) == 0:
            # individual files generated by run and put into scratch space, generate these on access
            # TODO: 202507 csk for Gustavo's code only?
            flywheel_labels = fws_separate_flywheel_labels(self.original_path)
            print(flywheel_labels)
            local_path = f'{self.get_common_path()}{os.path.sep}{flywheel_labels[2]}{os.path.sep}Baseline'
            self.local_paths = glob.glob(f'{local_path}{os.path.sep}*')

            for local_path in self.local_paths:
                output_paths.append(f'{os.path.dirname(self.original_path)}{os.path.sep}{os.path.basename(local_path)}')

        for local_path, output_path in zip(self.local_paths, output_paths):
            print('save_files', local_path, output_path)
            if fws_is_flywheel_path(output_path):
                 fws_upload_file_to_flywheel(fw_client, local_path=local_path, fw_path=output_path)
            else:
                shutil.copy(local_path, output_path)


