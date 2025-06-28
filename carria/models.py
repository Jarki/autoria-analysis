import dataclasses as dc


@dc.dataclass
class CarInfo:
    id: str
    make: str
    model: str
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