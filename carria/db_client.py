import abc
import datetime as dt

import duckdb
import pandas as pd

from . import models


class BaseDbClient(abc.ABC):
    @abc.abstractmethod
    def create_database(self):
        pass

    @abc.abstractmethod
    def insert_data(self, data: list[models.CarInfo]):
        pass


class DuckDbClient(BaseDbClient):
    def __init__(self, filename: str="carria.duckdb"):
        self.connection = duckdb.connect(database=filename)
    
    def create_database(self):
        sql = """
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY,
    added_at TIMESTAMP,
    updated_at TIMESTAMP,

    name VARCHAR,
    year INTEGER,
    generation VARCHAR,
    price INTEGER,
    mileage DOUBLE,
    location VARCHAR,
    engine VARCHAR,
    transmission VARCHAR,
    vin VARCHAR UNIQUE,
    plate VARCHAR,
    link VARCHAR,
    currency VARCHAR
);
CREATE SEQUENCE IF NOT EXISTS seq_carid START 1;
"""
        res = self.connection.execute(sql)
        return res

    def get_all(self) -> list[models.CarInfo]:
        res = self.connection.execute("SELECT * FROM cars")
        res = res.fetchall()
        return res
    
    def get_all_to_df(self) -> pd.DataFrame:
        info = self.get_all()
        names = [d[0] for d in self.connection.description]
        return pd.DataFrame(info, columns=names)

    def insert_data(self, data: list[models.CarInfo]):
        self.connection.executemany(
            """INSERT INTO cars 
            (id, added_at, updated_at,
             name, year, generation, price, mileage, location, engine, transmission, vin, plate, link, currency)
            VALUES (nextval('seq_carid'), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT (vin) DO UPDATE 
            SET (updated_at,
             name, year, generation, price, mileage, location, engine, transmission, vin, plate, link, currency)
             = ($2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)""",
            [(dt.datetime.now(), dt.datetime.now(),
             car.name, car.year, car.generation, car.price, car.mileage, car.location, car.engine, 
             car.transmission, car.vin, car.plate, car.link, car.currency)
             for car in data]
        )