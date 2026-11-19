class Ticket:
    def __init__(self, id: int, event_id: int, user_id: int, status: str, qr_code: str, created_at: str):
        self.id = id
        self.event_id = event_id
        self.user_id = user_id
        self.status = status
        self.qr_code = qr_code
        self.created_at = created_at
    
    def __str__(self):
        return f"Ticket(event_id={self.event_id}, user_id={self.user_id}, status='{self.status}')"