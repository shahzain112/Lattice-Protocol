import pandas as pd
import json
import os

class DataEngineCore:
    @staticmethod
    def process_batch(file_path: str, transform_rules: dict):
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            return df.to_dict(orient='records')
        return {"error": "File not found"}

    @staticmethod
    def aws_s3_ingest(bucket: str, key: str):
        return f"Simulating AWS ingestion from {bucket}/{key}"