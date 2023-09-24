import csv
import yaml


def get_config_from_yaml_file(full_file_path_and_name: str):
    return yaml.load(open(full_file_path_and_name, 'r'), Loader=yaml.FullLoader)


def get_data_from_csv_file(full_file_path_and_name: str):
    with open(full_file_path_and_name, newline='') as f:
        reader = csv.reader(f)
        data = [list(row) for row in reader]

    return data
