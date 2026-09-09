import os
from abc import ABC, abstractmethod
from datetime import datetime

class BaseRuleValidator(ABC):
    def __init__(self, dataset_name: str, dataset_dir: str, input_data_dir: str = None, dsd_dir: str = None, log_dir: str = "un_dataset_validator/logs"):
        self.dataset_name = dataset_name
        self.dataset_dir = dataset_dir
        self.input_data_dir = input_data_dir
        self.dsd_dir = dsd_dir
        
        # Standard directories derived from the dataset directory
        self.processed_dir = os.path.join(dataset_dir, "processed_data")
        self.pvmap_dir = os.path.join(dataset_dir, "pvmap")
        self.dc_generated_dir = os.path.join(dataset_dir, "dc_generated")
        self.schema_dir = os.path.join(dataset_dir, "schema")
        
        os.makedirs(log_dir, exist_ok=True)
        # Name logs like: rule1_sdg_q1-2026_validation.log
        rule_name_slug = self.__class__.__name__.replace('Validator', '').lower()
        self.log_file = os.path.join(log_dir, f"{rule_name_slug}_{self.dataset_name}_validation.log")
        
    def setup_logging(self, rule_title: str):
        with open(self.log_file, 'w', encoding='utf-8') as log:
            log.write(f"--- {rule_title} Validation Log ---\n")
            log.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write(f"Dataset: {self.dataset_name}\n")
            log.write(f"Dataset Directory: {self.dataset_dir}\n\n")

    def write_log(self, message: str):
        with open(self.log_file, 'a', encoding='utf-8') as log:
            log.write(f"{message}\n")

    @abstractmethod
    def validate(self):
        """Implement the core validation logic here."""
        pass
