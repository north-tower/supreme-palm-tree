import json
import os
from datetime import datetime

class UserManager:
    def __init__(self):
        self.users_file = 'data/users.json'
        self.admin_ids = set()  # Set of admin IDs
        self._ensure_data_directory()
        self._load_users()
        self._migrate_user_data()  # Add migration call

    def _migrate_user_data(self):
        """Migrate existing user data to include new fields"""
        updated = False
        for user_id, user in self.users.items():
            # Add is_active field if missing
            if 'is_active' not in user:
                user['is_active'] = True
                updated = True
            
            # Add is_admin field if missing
            if 'is_admin' not in user:
                user['is_admin'] = user_id in self.admin_ids
                updated = True
            
            # Add favorite_pairs field if missing
            if 'favorite_pairs' not in user:
                user['favorite_pairs'] = []
                updated = True
            
            # Ensure all required fields exist
            required_fields = {
                'username': None,
                'is_admin': False,
                'is_approved': False,
                'is_active': True,
                'signals_remaining': 3,
                'joined_date': datetime.now().isoformat()
            }
            
            for field, default_value in required_fields.items():
                if field not in user:
                    user[field] = default_value
                    updated = True
        
        if updated:
            self._save_users()
            print("✅ [INFO] User data migration completed successfully")

    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        try:
            os.makedirs('data', exist_ok=True)
            if not os.path.exists(self.users_file):
                self._save_users({})
        except Exception as e:
            print(f"⚠️ [ERROR] Failed to create data directory: {e}")
            # Try to create in current directory if data directory fails
            self.users_file = 'users.json'
            if not os.path.exists(self.users_file):
                self._save_users({})

    def _load_users(self):
        """Load users from the JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
                # Load admin IDs from users
                self.admin_ids = {
                    user_id for user_id, user in self.users.items()
                    if user.get('is_admin', False)
                }
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ [WARNING] Failed to load users file: {e}")
            self.users = {}
            self.admin_ids = set()
        except Exception as e:
            print(f"⚠️ [ERROR] Unexpected error loading users: {e}")
            self.users = {}
            self.admin_ids = set()

    def _save_users(self, users=None):
        """Save users to the JSON file"""
        if users is None:
            users = self.users
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=4)
        except Exception as e:
            print(f"⚠️ [ERROR] Failed to save users: {e}")
            # Try to save in current directory if data directory fails
            try:
                self.users_file = 'users.json'
                with open(self.users_file, 'w') as f:
                    json.dump(users, f, indent=4)
            except Exception as e2:
                print(f"⚠️ [ERROR] Failed to save users in fallback location: {e2}")

    def add_admin(self, admin_id):
        """Add a new admin"""
        admin_id = str(admin_id)
        if admin_id not in self.admin_ids:
            self.admin_ids.add(admin_id)
            if admin_id not in self.users:
                self.users[admin_id] = {
                    'is_admin': True,
                    'is_approved': True,
                    'is_active': True,
                    'signals_remaining': float('inf'),
                    'joined_date': datetime.now().isoformat(),
                    'favorite_pairs': []
                }
            else:
                self.users[admin_id]['is_admin'] = True
            self._save_users()
            return True
        return False

    def remove_admin(self, admin_id):
        """Remove an admin"""
        admin_id = str(admin_id)
        if admin_id in self.admin_ids:
            self.admin_ids.remove(admin_id)
            if admin_id in self.users:
                self.users[admin_id]['is_admin'] = False
            self._save_users()
            return True
        return False

    def is_admin(self, user_id):
        """Check if a user is an admin"""
        return str(user_id) in self.admin_ids

    def get_admins(self):
        """Get list of all admin IDs"""
        return list(self.admin_ids)

    def add_user(self, user_id, username=None):
        """Add a new user with trial signals"""
        if str(user_id) not in self.users:
            self.users[str(user_id)] = {
                'username': username,
                'is_admin': False,
                'is_approved': False,
                'is_active': True,
                'signals_remaining': 3,  # Trial signals
                'joined_date': datetime.now().isoformat(),
                'favorite_pairs': []
            }
            self._save_users()
            return True
        return False

    def get_user(self, user_id):
        """Get user information"""
        return self.users.get(str(user_id))

    def can_use_signal(self, user_id):
        """Check if user can use a signal"""
        user = self.get_user(user_id)
        if not user:
            return False
        # Check if user is active and has remaining signals
        if user['is_admin']:
            return user['is_active']  # Admins can always use signals if active
        return user['is_active'] and user['signals_remaining'] > 0

    def use_signal(self, user_id):
        """Use one signal from user's remaining signals"""
        user = self.get_user(user_id)
        if not user or not user['is_active']:
            return False
        # Don't decrement signals for admins
        if user['is_admin']:
            return True
        # For non-admins, check and decrement signals
        if user['signals_remaining'] > 0:
            user['signals_remaining'] -= 1
            self._save_users()
            return True
        return False

    def approve_user(self, user_id, admin_id):
        """Approve a user (admin only)"""
        if not self.is_admin(admin_id):
            return False, "Only admin can approve users"
        
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        user['is_approved'] = True
        user['is_active'] = True
        # Set signals based on user type
        if user.get('is_admin', False):
            user['signals_remaining'] = float('inf')  # Unlimited signals for admins
        else:
            user['signals_remaining'] = 100  # 100 signals for regular approved users
        self._save_users()
        return True, "User approved successfully"

    def activate_user(self, user_id, admin_id):
        """Activate a user (admin only)"""
        if not self.is_admin(admin_id):
            return False, "Only admin can activate users"
        
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if user['is_active']:
            return False, "User is already active"
        
        user['is_active'] = True
        self._save_users()
        return True, "User activated successfully"

    def deactivate_user(self, user_id, admin_id):
        """Deactivate a user (admin only)"""
        if not self.is_admin(admin_id):
            return False, "Only admin can deactivate users"
        
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if not user['is_active']:
            return False, "User is already deactivated"
        
        user['is_active'] = False
        self._save_users()
        return True, "User deactivated successfully"

    def get_pending_users(self):
        """Get list of pending users"""
        return {
            user_id: user for user_id, user in self.users.items()
            if not user['is_approved'] and not user['is_admin']
        }

    def get_user_stats(self, user_id):
        """Get user statistics"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        return {
            'username': user.get('username', 'Unknown'),
            'is_approved': user['is_approved'],
            'is_active': user['is_active'],
            'is_admin': user['is_admin'],
            'signals_remaining': user['signals_remaining'],
            'joined_date': user['joined_date']
        }

    def get_favorite_pairs(self, user_id):
        """Get user's favorite pairs"""
        user = self.get_user(user_id)
        return user.get('favorite_pairs', []) if user else []

    def add_favorite_pair(self, user_id, pair):
        """Add a pair to user's favorites"""
        user = self.get_user(user_id)
        if user and pair not in user.get('favorite_pairs', []):
            if 'favorite_pairs' not in user:
                user['favorite_pairs'] = []
            user['favorite_pairs'].append(pair)
            self._save_users()
            return True
        return False

    def remove_favorite_pair(self, user_id, pair):
        """Remove a pair from user's favorites"""
        user = self.get_user(user_id)
        if user and pair in user.get('favorite_pairs', []):
            user['favorite_pairs'].remove(pair)
            self._save_users()
            return True
        return False 