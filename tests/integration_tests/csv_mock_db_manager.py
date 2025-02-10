# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import csv
from collections import defaultdict


class CSVMockDatabaseManager:
    def __init__(self):
        self.data = defaultdict(list)
        self.current_query = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def execute_query(self, query, params=None):
        if query.lower().startswith("insert into"):
            table_name = query.split()[2]
            self.data[table_name].append(params)

    def fetch_one(self, query, params=None):
        return None

    def fetch_all(self, query, params=None):
        return []

    def write_to_csv(self):
        for table_name, rows in self.data.items():
            if rows:
                with open(f"{table_name}.csv", "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(rows[0].keys())  # Write header
                    for row in rows:
                        writer.writerow(row.values())

    def get_reader_db(self):
        return self

    def get_writer_db(self):
        return self

    def query(self, model):
        # Store the model being queried
        self.current_query = model
        return self

    def filter(self, *criterion):
        return self

    def filter_by(self, **kwargs):
        return []

    def first(self):
        return None

    def all(self):
        return []

    def commit(self):
        return None

    def refresh(self, obj):
        return None

    def one(self):
        return None

    def add(self, obj):
        # In a real database, this would add the object to the session
        # For our mock, we'll just store it in our data structure
        table_name = obj.__class__.__name__
        self.data[table_name].append(obj.__dict__)
        return self
