#!/usr/bin/env python3
"""
EventHub API uç noktaları için sahte veriler oluşturmaya yarayan komut dosyası.
Bu komut dosyası, app/api dizinindeki JSON dosyalarını okur ve 
API testleri için sahte yanıtlar sağlamak amacıyla kullanılabilir.
"""

import json
import os

# Sahte verilerin (mock data) nerede bulunduğu
MOCK_DATA_DIR = "api"

def load_mock_data(filename):
    """Load mock data from a JSON file."""
    try:
        with open(os.path.join("app", MOCK_DATA_DIR, filename), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found in {MOCK_DATA_DIR}")
        return []

def get_venues():
    """Get mock venue data."""
    return load_mock_data("venues.json")

def get_users():
    """Get mock user data."""
    return load_mock_data("users.json")

def get_events():
    """Get mock event data."""
    return load_mock_data("events.json")

def get_seats():
    """Get mock seat data."""
    return load_mock_data("seats.json")

def get_tickets():
    """Get mock ticket data."""
    return load_mock_data("tickets.json")

def get_payments():
    """Get mock payment data."""
    return load_mock_data("payments.json")

def get_reservations():
    """Get mock reservation data."""
    return load_mock_data("reservations.json")

def get_reservation_seats():
    """Get mock reservation seat data."""
    return load_mock_data("reservation_seats.json")

# Örnek kullanım
if __name__ == "__main__":
    print("Loading mock data for EventHub API...")
    
    venues = get_venues()
    users = get_users()
    events = get_events()
    seats = get_seats()
    tickets = get_tickets()
    payments = get_payments()
    reservations = get_reservations()
    reservation_seats = get_reservation_seats()
    
    print(f"Loaded {len(venues)} venues")
    print(f"Loaded {len(users)} users")
    print(f"Loaded {len(events)} events")
    print(f"Loaded {len(seats)} seats")
    print(f"Loaded {len(tickets)} tickets")
    print(f"Loaded {len(payments)} payments")
    print(f"Loaded {len(reservations)} reservations")
    print(f"Loaded {len(reservation_seats)} reservation seats")
    
    # Örnek olarak ilk kayıtları yazdır
    if venues:
        print("\nFirst venue:", venues[0])
    if users:
        print("First user:", users[0])
    if events:
        print("First event:", events[0])
    if seats:
        print("First seat:", seats[0])
    if tickets:
        print("First ticket:", tickets[0])
    if payments:
        print("First payment:", payments[0])
    if reservations:
        print("First reservation:", reservations[0])
    if reservation_seats:
        print("First reservation seat:", reservation_seats[0])