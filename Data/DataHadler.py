import json
import os

import numpy as np


class DataHandler:
    def __init__(self, output_folder, parameters_file):
        self.output_folder = output_folder
        self.parameters_file = parameters_file
        os.makedirs(self.output_folder, exist_ok=True)

    def save_parameters(self, parameters):
        """Сохраняет параметры модели в файл JSON."""
        with open(self.parameters_file, "w") as file:
            json.dump(parameters, file, indent=4)
        print(f"Model parameters saved to {self.parameters_file}")

    def load_parameters(self):
        """Загружает параметры модели из файла JSON."""
        if not os.path.exists(self.parameters_file):
            raise FileNotFoundError(f"Parameters file {self.parameters_file} not found.")
        with open(self.parameters_file, "r") as file:
            parameters = json.load(file)
        print(f"Loaded model parameters from {self.parameters_file}")
        return parameters

    def save_temperature(self, step, temperature_data, file_prefix="temperature_step"):
        """Сохраняет данные температуры в файл .npy."""
        filename = os.path.join(self.output_folder, f"{file_prefix}_{step}.npy")
        np.save(filename, temperature_data)
        print(f"Saved step {step} to {filename}")

    def load_temperature_files(self):
        """Загружает список файлов с температурами."""
        files = [f for f in os.listdir(self.output_folder) if f.endswith(".npy")]
        return sorted(files, key=lambda x: int(x.split('_')[-1].split('.')[0]))