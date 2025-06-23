import json
import os
from datetime import datetime
from threading import Lock

class TransactionLogger:
    def __init__(self, filename='transactions.json'):
        self.filename = filename
        self.lock = Lock()
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)

    def add_transaction(self, user_id, pair, expiration, analysis, indicators, signal):
        transaction = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'pair': pair,
            'expiration': expiration,
            'analysis': analysis,
            'indicators': indicators,
            'signal': signal,
            'result': 'pending'
        }
        with self.lock:
            transactions = self._load_all()
            transactions.append(transaction)
            self._save_all(transactions)
        return len(transactions) - 1  # Return index as transaction ID

    def update_result(self, transaction_id, result):
        with self.lock:
            transactions = self._load_all()
            if 0 <= transaction_id < len(transactions):
                transactions[transaction_id]['result'] = result
                self._save_all(transactions)
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
            return self._load_all() 