"""
Kimlik ve Oturum Yönetim Servisi
BR-1.1: Katılımcı (participant), Organizatör (organizer), Yönetici (admin)
"""
from src.models.user import User

class AuthService:
    def __init__(self):
        self.users = {
            "user-101": User(
                id="user-101",
                name="Berk Yılmaz",
                email="berk@eventhub.com",
                phone="+90 555 123 4567",
                role="participant",
                is_student=True
            ),
            "admin-1": User(
                id="admin-1",
                name="Sistem Yöneticisi",
                email="admin@eventhub.com",
                phone="+90 555 999 8877",
                role="admin",
                is_student=False
            )
        }
        self.current_user: User = self.users["user-101"]

    def switch_role(self, role: str):
        if role == "admin":
            self.current_user = self.users["admin-1"]
        else:
            self.current_user = self.users["user-101"]

    def toggle_student(self) -> bool:
        self.current_user.is_student = not self.current_user.is_student
        return self.current_user.is_student

auth_service = AuthService()
