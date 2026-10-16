import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from repositories.database import Database
from helpers.utils import get_datetime_local
from helpers.constants import AUDIT_COLUMNS_SQL, AUDIT_COLUMN_CREATED_AT


class StructuredRepository():
    table_name: str = ""
    schema_sql: str = ""
    id_column: str = ""

    def __init__(self, db: Database):
        self.db = db

    def setup(self):
        schema = (
            f"{self.schema_sql.rstrip().rstrip(',')}, "
            f"{AUDIT_COLUMNS_SQL}"
        )

        self.db.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} ({schema});")
        print(f"Table '{self.table_name}' ready.")


    def insert(self, fields: dict):
        fields["created_at"] = get_datetime_local()
        fields.pop("updated_at", None)

        cols = ", ".join(fields.keys())
        placeholders = ", ".join(["%s"] * len(fields))

        res = self.db.execute(
            f"""INSERT INTO {self.table_name} 
                ({cols}) VALUES ({placeholders})
                RETURNING {self.id_column};""",
            tuple(fields.values())
        )

        return res

    def get_latest_data(self):
        row = self.db.fetch_one(f"""SELECT *
                                  FROM {self.table_name} 
                                  ORDER BY {AUDIT_COLUMN_CREATED_AT} DESC 
                                  LIMIT 1;""")
        if not row:
            return None
    
        return row 


    def update(self, row_id, **fields):
        fields.pop("created_at", None)
        fields["updated_at"] = get_datetime_local()

        set_clause = ", ".join(f"{k} = %s" for k in fields)

        res = self.db.fetch_one(
            f"""UPDATE {self.table_name} 
              SET {set_clause} 
              WHERE {self.id_column} = %s 
              RETURNING *;""",
            (*fields.values(), row_id),
        )

        return res

 
    def get_by_id(self, row_id):
        row = self.db.fetch_one(f"""SELECT * 
                                  FROM {self.table_name} 
                                  WHERE {self.id_column} = %s;""", 
                            (row_id,))
        if not row:
            return None
        
        return row
 
    def get_all(self):
       rows = self.db.fetch_all(f"""SELECT * 
                                  FROM {self.table_name};""")
       return rows