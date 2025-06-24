import dataclasses as dc


@dc.dataclass
class CarInfo:
    name: str
    year: int
    generation: str
    price: int
    mileage: int
    location: str
    engine: str
    transmission: str
    vin: str
    plate: str
    link: str
    currency: str