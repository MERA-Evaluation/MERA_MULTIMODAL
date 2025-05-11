import os
import argparse

import yaml
from main import main

parser = argparse.ArgumentParser()
parser.add_argument("--prefix", "-p", type=str, required=True)

args, unknown = parser.parse_known_args()


with open("./template_config.yml", "r") as file:
    data = yaml.safe_load(file)
    data["storage_params"]["prefix"] = args.prefix
    x = data["storage_params"]["result_file_name"]
    result_file_name = os.path.join(
        args.prefix, data["storage_params"]["result_file_name"]
    )
    data["storage_params"]["result_file_name"] = result_file_name
    failed_samples_folder = os.path.join(
        args.prefix, data["checkout_params"]["failed_samples_folder"]
    )
    data["checkout_params"]["failed_samples_folder"] = failed_samples_folder

    with open("./config.yml", "w") as file:
        yaml.dump(data, file)

    main()
    #  os.system("conda activate ./.tests_env")
    # os.system("python3 main.py")

    # os.remove("./config.yml")
