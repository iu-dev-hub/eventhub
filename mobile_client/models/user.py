class User:
    def __init__(self, id: int, first_name: str, last_name: str, email: str, role: str, is_student: bool, 
                 student_number: str, notify_email: bool, avatar_url: str, created_at: str, approved: bool = False):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role
        self.is_student = is_student
        self.student_number = student_number
        self.notify_email = notify_email
        self.avatar_url = avatar_url
        self.created_at = created_at
        self.approved = approved
    
    def __str__(self):
        return f"User(first_name='{self.first_name}', last_name='{self.last_name}', email='{self.email}')"