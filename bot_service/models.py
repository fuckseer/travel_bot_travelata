from dataclasses import dataclass

@dataclass
class Tour:
    id: int
    hotel_name: str
    nights: int
    price: int
    url: str
    check_in: str

