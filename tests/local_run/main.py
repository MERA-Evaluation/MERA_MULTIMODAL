import os
import sys
from typing import Any, Optional

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.extend(
    [
        os.path.join(base_dir, "utils"),
        os.path.join(base_dir, "base"),
        os.path.join(base_dir, "filters"),
    ]
)

import yaml
import docker

from di import get_runner_collector
from checkouts.base.checkout_runner import CheckoutRunner


def check_docker_is_running():
    try:
        client = docker.from_env()
        client.version()
        return True
    except Exception:
        return False


def read_yaml(path_to_config: str = "./config.yml"):
    with open(path_to_config) as stream:
        try:
            content = yaml.safe_load(stream)
            return content
        except yaml.YAMLError as exc:
            print(f"Error: {exc}")


def path_validation(path_to_map: str):
    """
    Check path to DEPP entity exists.
    Parameters
    ----------
    path_to_map

    Returns
    -------

    """
    return os.path.exists(path_to_map)


def format_params(map_params: dict[str, str | int]) -> str:
    """
    Convert params from YAML config to str format.
    Parameters
    ----------
    map_params

    Returns
    -------

    """
    map_params_str = " "
    for key, value in map_params.items():
        map_params_str += f"--{key}={value} "
    return map_params_str + "--is_use_k8s_mount=0"


def prepare_input_data(content: dict[str, Any]):
    path_to_map_runner = "{map_type}s/{map_modality}/{map_name}/run.py".format(
        map_modality=content.get("map_modality"),
        map_name=content.get("map_name"),
        map_type=content.get("map_type"),
    )
    path_to_map_runner = os.path.join(os.getcwd(), path_to_map_runner)
    map_config_str = format_params(content)
    return path_to_map_runner, map_config_str


def local_run(
    path_to_map_runner: str, map_config_str: str, volume_folder: Optional[str] = None
) -> None:
    command = "python3 {path_to_map_runner} {map_config}"
    if path_validation(path_to_map_runner):
        command = command.format(
            path_to_map_runner=path_to_map_runner, map_config=map_config_str
        )
        os.system(command)
    else:
        raise OSError("incorrect path to Depp map runner")


def docker_run(
    path_to_map_runner: str, map_config_str: str, volume_folder: Optional[str]
) -> None:
    if path_validation(path_to_map_runner):
        depp_map_name = path_to_map_runner.split("/")[-2]
        depp_map_type = path_to_map_runner.split("/")[-4][:-1]
        path_to_dockerfile = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    else:
        raise OSError("incorrect path to Depp map runner")

    if check_docker_is_running():
        docker_image = f"swr.ru-moscow-1.hc.sbercloud.ru/sber_devices/rnd_de/depp/{depp_map_type}_{depp_map_name}:dev"
        try:
            path_to_dockerfile = os.path.join(
                path_to_dockerfile, f"Dockerfile.{depp_map_type}_{depp_map_name}"
            )
            docker_build_command = (
                f"docker build . -t {docker_image} -f {path_to_dockerfile}"
            )
            os.system(docker_build_command)
        except Exception as err:
            raise Exception(f"Docker build error {err}")
        volume_str = f"-v {volume_folder}:{volume_folder}" if volume_folder else ""
        docker_run_command = f"docker run --rm {volume_str} {docker_image} python run.py {map_config_str}"
        os.system(docker_run_command)
    else:
        raise Exception("Docker daemon is not running")


def get_storage_params(content: dict[str, Any]) -> dict[str, Any]:
    return content.get("storage_params", {})


def get_docker_params(content: dict[str, Any]) -> str:
    volume_folder = content.get("storage_params", {}).get("prefix")
    return volume_folder


def run_depp():
    content = read_yaml()

    storage_params = get_storage_params(content)

    # stage to validate paths

    if not storage_params:
        raise KeyError("Storage params should be passed")
    volume_folder = get_docker_params(content)
    filters_params = content.get("map_params")
    checkout_params = content.get("checkout_params")
    run_type_params = content.get("type_get_keys", {})
    run_type = run_type_params.get("type_pagination")
    if not run_type:
        raise KeyError("Run type parameter must be passed")
    if filters_params:
        run_type_function = docker_run if "docker" in run_type else local_run
        filters = [
            filter_data.get("map_name").replace("_", "")
            for filter_data in filters_params
        ]

        collector = get_runner_collector(
            run_type.split("_")[0],
            storage_params.get("prefix"),
            filters,
            storage_params.get("prefix"),
            storage_params.get("result_file_name"),
            **storage_params,
        )
        if not run_type:
            print("Fill the field type_get_keys/type_pagination")
        os.chdir("..")
        for filter_params in filters_params:
            content = {**storage_params, **filter_params, **run_type_params}
            path_to_map_runner, map_config_str = prepare_input_data(content)
            run_type_function(path_to_map_runner, map_config_str, volume_folder)
        collector.run()
    if checkout_params:
        checkout_project = checkout_params.get("project")
        checkouts = checkout_params.get("checkouts")
        all_checkouts_result_file = checkout_params.get("checkout_result_file")
        if checkout_params and (not checkout_project and not checkouts):
            raise ValueError(
                "To perform the checkouts, you must fill the field 'checkout_params/project or "
                "checkout_params/checkouts'"
            )
        else:
            checkout_runner = CheckoutRunner(
                run_type.split("_")[0],
                checkout_project,
                checkouts,
                all_checkouts_result_file=all_checkouts_result_file,
                **storage_params,
            )
            checkout_runner.run()


def main():
    run_depp()


if __name__ == "__main__":
    main()
