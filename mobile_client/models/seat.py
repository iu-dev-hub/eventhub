class Seat:
    def __init__(self, id: int, event_id: int, seat_code: str, status: str, locked_until: str):
        self.id = id
        self.event_id = event_id
        self.seat_code = seat_code
        self.status = status
        self.locked_until = locked_until
    
    def __str__(self):
        return f"Seat(seat_code='{self.seat_code}', status='{self.status}')"