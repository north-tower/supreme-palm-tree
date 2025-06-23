import json
import os
from datetime import datetime
import uuid

class SupportManager:
    def __init__(self):
        self.tickets_file = 'data/support_tickets.json'
        self._ensure_data_directory()
        self._load_tickets()

    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        try:
            os.makedirs('data', exist_ok=True)
            if not os.path.exists(self.tickets_file):
                self._save_tickets({})
        except Exception as e:
            print(f"⚠️ [ERROR] Failed to create data directory: {e}")
            self.tickets_file = 'support_tickets.json'
            if not os.path.exists(self.tickets_file):
                self._save_tickets({})

    def _load_tickets(self):
        """Load tickets from the JSON file"""
        try:
            with open(self.tickets_file, 'r') as f:
                self.tickets = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ [WARNING] Failed to load tickets file: {e}")
            self.tickets = {}
        except Exception as e:
            print(f"⚠️ [ERROR] Unexpected error loading tickets: {e}")
            self.tickets = {}

    def _save_tickets(self, tickets=None):
        """Save tickets to the JSON file"""
        if tickets is None:
            tickets = self.tickets
        try:
            with open(self.tickets_file, 'w') as f:
                json.dump(tickets, f, indent=4)
        except Exception as e:
            print(f"⚠️ [ERROR] Failed to save tickets: {e}")

    def create_ticket(self, user_id, username=None, category=None, priority=None):
        """Create a new support ticket with category and priority"""
        ticket_id = str(uuid.uuid4())[:8]
        self.tickets[ticket_id] = {
            'user_id': str(user_id),
            'username': username,
            'category': category,
            'priority': priority,
            'status': 'open',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': []
        }
        self._save_tickets()
        return ticket_id

    def add_message(self, ticket_id, user_id, message, is_admin=False):
        """Add a message to a ticket"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        ticket['messages'].append({
            'user_id': str(user_id),
            'is_admin': is_admin,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        ticket['updated_at'] = datetime.now().isoformat()
        self._save_tickets()
        return True

    def close_ticket(self, ticket_id):
        """Close a support ticket"""
        if ticket_id not in self.tickets:
            return False
        
        self.tickets[ticket_id]['status'] = 'closed'
        self.tickets[ticket_id]['updated_at'] = datetime.now().isoformat()
        self._save_tickets()
        return True

    def reopen_ticket(self, ticket_id):
        """Reopen a closed ticket"""
        if ticket_id not in self.tickets:
            return False
        
        self.tickets[ticket_id]['status'] = 'open'
        self.tickets[ticket_id]['updated_at'] = datetime.now().isoformat()
        self._save_tickets()
        return True

    def get_ticket(self, ticket_id):
        """Get ticket information"""
        return self.tickets.get(ticket_id)

    def get_user_tickets(self, user_id):
        """Get all tickets for a user"""
        return {
            ticket_id: ticket for ticket_id, ticket in self.tickets.items()
            if str(ticket['user_id']) == str(user_id)
        }

    def get_all_tickets(self):
        """Get all tickets"""
        return self.tickets

    def get_open_tickets(self):
        """Get all open tickets"""
        return {
            ticket_id: ticket for ticket_id, ticket in self.tickets.items()
            if ticket['status'] == 'open'
        }

    def get_ticket_status(self, ticket_id):
        """Get ticket status"""
        ticket = self.tickets.get(ticket_id)
        return ticket['status'] if ticket else None 