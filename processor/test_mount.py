def fws_get_mounted_path(file_path: str) -> str:
    """
    helper to get the ultimate path of a mounted filesystem. Sometimes we need it to decide where to load/save things

    Parameters
    ----------
    file_path: str
        The file path to test

    Returns
    The ultimate "source" path of the file, can be different if on a mounted drive
    -------

    """
    print("fws_get_mounted_path", file_path)
    try:
        with open('/proc/mounts', 'r') as mounts_file:
            for line in mounts_file:
                # find the device/mountpoint for this path and replace it
                if 'DICOM' in line:
                    print("<<<<", line)
                parts = line.split()
                device = parts[0]
                mount_point = parts[1]
                # print(">>>", device, mount_point)
                if device in file_path:
                    return file_path.replace(device, mount_point)

    except FileNotFoundError:
        # no mount point, just return the path
        print("no path?")
        return file_path

tmp = fws_get_mounted_path('/home/aa-cxk023/seg')

print(tmp)