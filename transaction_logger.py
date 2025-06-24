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
        """Export all transactions to an Excel file, including detailed indicator data."""
        if not filename:
            filename = f'transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        if not self.transactions:
            print("No transactions to export.")
            return None

        # --- Data Preparation ---
        records = []
        for idx, t in enumerate(self.transactions):
            # Basic info
            record = {
                'Transaction ID': t.get('id', idx + 1),
                'Date & Time': t.get('timestamp'),
                'User ID': t.get('user_id'),
                'Currency Pair': t.get('pair'),
                'Expiration (min)': t.get('expiration'),
                'Signal': t.get('signal', '').upper(),
                'Result': t.get('result', 'PENDING').upper(),
                'Analysis Summary': t.get('analysis', '')
            }
            
            # Unpack the 'indicators' dictionary into separate columns
            indicators = t.get('indicators', {})
            if isinstance(indicators, dict):
                for key, value in indicators.items():
                    # Sanitize key for column header
                    col_name = f"Indicator: {key}"
                    record[col_name] = str(value) # Convert all to string to avoid type issues in Excel
            
            records.append(record)

        # --- DataFrame Creation ---
        df = pd.DataFrame(records)
        
        # --- Formatting ---
        # Format timestamp
        df['Date & Time'] = pd.to_datetime(df['Date & Time'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

        # Define the desired column order, putting indicators at the end
        base_columns = [
            'Transaction ID', 'Date & Time', 'User ID', 'Currency Pair', 
            'Expiration (min)', 'Signal', 'Result', 'Analysis Summary'
        ]
        
        # Get all unique indicator columns from the dataframe
        indicator_columns = sorted([col for col in df.columns if col.startswith('Indicator:')])
        
        # Combine and ensure all columns exist, filling missing with empty string
        final_columns = base_columns + indicator_columns
        for col in final_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Reorder the DataFrame
        df = df[final_columns]

        # --- Export ---
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"✅ Successfully exported {len(records)} transactions to {filename}")
        return filename 