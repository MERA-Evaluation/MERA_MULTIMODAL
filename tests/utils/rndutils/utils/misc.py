import logging
import os
import sys
from typing import Optional, Union

logger = logging.getLogger(__name__)


def find_dataset(
    datapath: str,
    extensions: Union[str, tuple] = "",
    only_filenames: bool = False,
    skip_formats: Optional[Union[str, tuple]] = None,
) -> list:
    """Explore dataset directory and find files by pattern

    Parameters
    ----------
    datapath : str
        Path to dataset or single file. Example: "../../dataset/" or "data/example.txt"
    extensions : Union[str, tuple]
        Template for file extentions ("*.mp4, *.mov etc.). Can be string or list of strings.
    only_filenames : bool
        Drop file extensions, return only filenames
    skip_formats : Union[str, tuple]
        Skip formats for dataset

    Returns
    -------
        list of files from datapath folder

    """

    # For single file return list with this item
    if os.path.isfile(datapath):
        if only_filenames:
            return [os.path.basename(os.path.splitext(datapath)[0])]
        return [datapath]

    # Find dataset recursevly
    dataset = sorted(
        [
            val
            for sublist in [
                [os.path.join(i[0], j) for j in i[2]] for i in os.walk(datapath)
            ]
            for val in sublist
            if val.lower().endswith(extensions)
        ]
    )

    # Skip unsupported formats if needed
    if skip_formats is not None:
        all_list, all_skip = [], []
        for item in dataset:
            if item.endswith(skip_formats):
                all_skip.append(item)
            else:
                all_list.append(item)
        dataset = all_list
        if all_skip:
            logger.info(
                f"Skipped files: {all_skip} because of passing skip fromats: {skip_formats}"
            )

    # Remove filepath and extensions if needed
    if only_filenames:
        return [os.path.basename(os.path.splitext(item)[0]) for item in dataset]

    return dataset


def walk_dataset(datapath: str, extensions: Union[str, tuple] = "") -> list:
    """Find files from datapath

    Parameters
    ----------
    datapath : str
        Path to dataset or single file. Example: "../../dataset/" or "data/example.txt"
    extensions : Union[str, tuple]
        Template for file extentions ("*.mp4, *.mov etc.). Can be string or list of strings.

    Returns
    -------
        list of files from datapath folder

    """

    # For single file return list with this item
    if os.path.isfile(datapath):
        return [datapath]

    # Find dataset recursevly
    dataset = sorted(
        [
            val
            for sublist in [
                [os.path.join(i[0].replace(datapath, ""), j) for j in i[2]]
                for i in os.walk(datapath)
            ]
            for val in sublist
            if val.lower().endswith(extensions)
        ]
    )

    if len(set(dataset)) != len(dataset):
        logger.warning(f"Some files has the same name into: {datapath}")

    return dataset


def count_files_by_extension(files_list: list) -> dict:
    """Count unique files by extensions.

    Parameters
    ----------
    files_list : list
        list of files. Example: ["data1.mp4, "data2.mov", "data3.mp4]

    Returns
    -------
        dict of counted elements.

    """
    count: dict[str, int] = {}
    for data in files_list:
        file_name, file_ext = os.path.splitext(data.lower())
        if file_ext not in count:
            count[file_ext] = 1
        else:
            count[file_ext] += 1
    count["total"] = sum(count.values())

    return count


def to_even(x):
    """Round to even"""
    return (x // 2) * 2


def remove_source_path(source: str, dataset: list) -> list:
    """Remove source path from dataset names e.g. source = "a/", dataset = ["a/b/c.tmp"] -> ["b/c.tmp"]

    Parameters
    ----------
    source : str
        Path to dataset. Example: "dataset/"
    dataset : list
        Template for file extentions ("*.mp4, *.mov etc.). Can be string or tuple of strings.

    Returns
    -------
        List of files without source path
    """
    source = os.path.join(source, "")
    return [data.replace(source, "") for data in dataset]


def dict_to_readable_string(data: dict) -> str:
    """Convert dictionary to readable string for logging.

    Parameters
    ----------
    data : dict
        Simple dict as key: value structure.

    Returns
    -------
    str
        Formatted string for printing and logging.

    """
    return "\n".join([f"{k :<30} : {v}" for k, v in data.items()])


def list_to_readable_string(data: list) -> str:
    """Convert list to readable string for logging.

    Parameters
    ----------
    data : list

    Returns
    -------
    str
        Formatted string for printing and logging.

    """
    return "\n".join([k for k in data])


def query_yes_no(
    question: str, default: str = "yes", force_yes: bool = False, force_no: bool = False
) -> bool:
    """Ask a yes/no question via raw_input() and return their answer.

    Parameters
    ----------
    question : str
        Question is a string that is presented to the user.
    default : str
        Default is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning an answer is required of the user).
    force_yes: bool
        Forced "yes" condition. Return True result if presented.
    force_no: bool
        Forced "no" condition. Return False result if presented.

    Returns
    -------
    bool
        True for Yes, False for No.

    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        if force_yes and not force_no:
            return True
        elif force_no and not force_yes:
            return False
        else:
            sys.stdout.write(question + prompt)
            choice = input().lower()
            if default is not None and choice == "":
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write(
                    "Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n"
                )
