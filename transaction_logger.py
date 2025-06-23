import json
import os
from datetime import datetime
from threading import Lock
import pandas as pd

class TransactionLogger:
    def __init__(self, filename='transactions.json'):
        self.filename = filename
        self.lock = Lock()
        self.load_transactions()

    def load_transactions(self):
        try:
            with open(self.filename, 'r') as f:
                self.transactions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.transactions = []
            self.save_transactions()

    def save_transactions(self):
        with open(self.filename, 'w') as f:
            json.dump(self.transactions, f, indent=2)

    def add_transaction(self, user_id, pair, expiration, analysis, indicators, signal):
        transaction = {
            'id': len(self.transactions) + 1,
            'user_id': user_id,
            'pair': pair,
            'expiration': expiration,
            'analysis': analysis,
            'indicators': indicators,
            'signal': signal,
            'result': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        with self.lock:
            self.transactions.append(transaction)
            self.save_transactions()
        return transaction['id']

    def update_result(self, transaction_id, result):
        with self.lock:
            for idx, transaction in enumerate(self.transactions):
                # Match by 'id' if present, else by index+1
                if ('id' in transaction and transaction['id'] == transaction_id) or \
                   ('id' not in transaction and idx + 1 == transaction_id):
                    transaction['result'] = result
                    self.save_transactions()
                    return True
            return False

    def _load_all(self):
        with open(self.filename, 'r') as f:
            return json.load(f)

    def _save_all(self, transactions):
        with open(self.filename, 'w') as f:
            json.dump(transactions, f, indent=2)

    def get_all(self):
        with self.lock:
            return self.transactions

    def export_to_excel(self, filename=None):
        """Export all transactions to an Excel file, filling missing columns if needed"""
        if not filename:
            filename = f'transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        # Define required columns and their default values
        required_columns = {
            'id': None,  # Will fill with index+1 if missing
            'timestamp': '',
            'pair': '',
            'expiration': '',
            'signal': '',
            'result': 'PENDING',
            'user_id': ''
        }

        # Prepare transactions with all required columns
        fixed_transactions = []
        for idx, t in enumerate(self.transactions):
            fixed = t.copy()
            for col, default in required_columns.items():
                if col not in fixed or fixed[col] == '':
                    if col == 'id':
                        fixed['id'] = idx + 1
                    elif col == 'result':
                        fixed['result'] = t.get('result', 'PENDING').upper()
                    else:
                        fixed[col] = default
            fixed_transactions.append(fixed)

        # Convert to DataFrame
        df = pd.DataFrame(fixed_transactions)

        # Reorder and rename columns for better readability
        columns = {
            'id': 'Transaction ID',
            'timestamp': 'Date & Time',
            'pair': 'Currency Pair',
            'expiration': 'Expiration (min)',
            'signal': 'Signal',
            'result': 'Result',
            'user_id': 'User ID'
        }

        # Select and rename columns
        df = df[list(columns.keys())].rename(columns=columns)

        # Format timestamp
        df['Date & Time'] = pd.to_datetime(df['Date & Time'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

        # Capitalize result and signal
        df['Result'] = df['Result'].str.upper()
        df['Signal'] = df['Signal'].str.upper()

        # Export to Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        return filename 