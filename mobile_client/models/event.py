"""Event data model for mobile client (TG-162)."""


class Event:
    def __init__(
        self,
        id: int,
        title: str,
        category: str,
        venue_id: int,
        start_time: str,
        end_time: str,
        capacity: int,
        price: float,
        status: str,
        organizer_id: int,
    ):
        self.id = id
        self.title = title
        self.category = category
        self.venue_id = venue_id
        self.start_time = start_time
        self.end_time = end_time
        self.capacity = capacity
        self.price = price
        self.status = status
        self.organizer_id = organizer_id

    def __str__(self):
        return (
            f"Event(title='{self.title}', start_time='{self.start_time}', "
            f"status='{self.status}')"
        )
