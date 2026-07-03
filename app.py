#!/usr/bin/env python3
"""
Professional Double-Entry Accounting System
"""

import json
import os
import sys
from datetime import datetime
from decimal import Decimal, getcontext, InvalidOperation
from typing import Dict, List, Tuple, Optional, Any

getcontext().prec = 28

# ============================================
# CONSTANTS
# ============================================
VERSION = "1.0.0"
DATA_DIR = "data"
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounting_data.json")
JOURNAL_FILE = os.path.join(DATA_DIR, "journal_entries.json")

ACCOUNT_TYPES = {
    'ASSET': 'Asset',
    'LIABILITY': 'Liability',
    'EQUITY': 'Equity',
    'INCOME': 'Income',
    'EXPENSE': 'Expense'
}

# Default Chart of Accounts
DEFAULT_ACCOUNTS = {
    # Assets (1xxx)
    '1000': {'name': 'Cash', 'type': 'ASSET', 'normal_balance': 'debit'},
    '1010': {'name': 'Bank Account', 'type': 'ASSET', 'normal_balance': 'debit'},
    '1020': {'name': 'Accounts Receivable', 'type': 'ASSET', 'normal_balance': 'debit'},
    '1030': {'name': 'Inventory', 'type': 'ASSET', 'normal_balance': 'debit'},
    '1040': {'name': 'Prepaid Expenses', 'type': 'ASSET', 'normal_balance': 'debit'},
    '1050': {'name': 'Fixed Assets', 'type': 'ASSET', 'normal_balance': 'debit'},
    '1060': {'name': 'Accumulated Depreciation', 'type': 'ASSET', 'normal_balance': 'credit'},
    '1070': {'name': 'Investments', 'type': 'ASSET', 'normal_balance': 'debit'},
    
    # Liabilities (2xxx)
    '2000': {'name': 'Accounts Payable', 'type': 'LIABILITY', 'normal_balance': 'credit'},
    '2010': {'name': 'Accrued Expenses', 'type': 'LIABILITY', 'normal_balance': 'credit'},
    '2020': {'name': 'Bank Loan', 'type': 'LIABILITY', 'normal_balance': 'credit'},
    '2030': {'name': 'Tax Payable', 'type': 'LIABILITY', 'normal_balance': 'credit'},
    '2040': {'name': 'Unearned Revenue', 'type': 'LIABILITY', 'normal_balance': 'credit'},
    '2050': {'name': 'Mortgage Payable', 'type': 'LIABILITY', 'normal_balance': 'credit'},
    
    # Equity (3xxx)
    '3000': {'name': "Owner's Capital", 'type': 'EQUITY', 'normal_balance': 'credit'},
    '3010': {'name': 'Retained Earnings', 'type': 'EQUITY', 'normal_balance': 'credit'},
    '3020': {'name': 'Drawings', 'type': 'EQUITY', 'normal_balance': 'debit'},
    '3030': {'name': 'Common Stock', 'type': 'EQUITY', 'normal_balance': 'credit'},
    
    # Income (4xxx)
    '4000': {'name': 'Service Revenue', 'type': 'INCOME', 'normal_balance': 'credit'},
    '4010': {'name': 'Sales Revenue', 'type': 'INCOME', 'normal_balance': 'credit'},
    '4020': {'name': 'Interest Income', 'type': 'INCOME', 'normal_balance': 'credit'},
    
    # Expenses (5xxx)
    '5000': {'name': 'Rent Expense', 'type': 'EXPENSE', 'normal_balance': 'debit'},
    '5010': {'name': 'Utilities Expense', 'type': 'EXPENSE', 'normal_balance': 'debit'},
    '5020': {'name': 'Salaries Expense', 'type': 'EXPENSE', 'normal_balance': 'debit'},
    '5030': {'name': 'Office Supplies', 'type': 'EXPENSE', 'normal_balance': 'debit'},
    '5040': {'name': 'Insurance Expense', 'type': 'EXPENSE', 'normal_balance': 'debit'},
    '5050': {'name': 'Depreciation Expense', 'type': 'EXPENSE', 'normal_balance': 'debit'},
    '5060': {'name': 'Interest Expense', 'type': 'EXPENSE', 'normal_balance': 'debit'},
    '5070': {'name': 'Tax Expense', 'type': 'EXPENSE', 'normal_balance': 'debit'},
    '5080': {'name': 'General & Administrative', 'type': 'EXPENSE', 'normal_balance': 'debit'},
}

# ============================================
# CLASSES
# ============================================

class Account:
    def __init__(self, code: str, name: str, account_type: str, normal_balance: str):
        self.code = code
        self.name = name
        self.type = account_type
        self.normal_balance = normal_balance
        self.balance = Decimal('0')
    
    def to_dict(self) -> Dict:
        return {
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'normal_balance': self.normal_balance,
            'balance': str(self.balance)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Account':
        account = cls(
            data['code'],
            data['name'],
            data['type'],
            data['normal_balance']
        )
        account.balance = Decimal(data.get('balance', '0'))
        return account

class JournalEntry:
    def __init__(self, entry_id: int, date: str, description: str, lines: List[Dict]):
        self.id = entry_id
        self.date = date
        self.description = description
        self.lines = lines
    
    def validate(self) -> bool:
        total_debit = sum(line['debit'] for line in self.lines)
        total_credit = sum(line['credit'] for line in self.lines)
        return total_debit == total_credit
    
    def get_totals(self) -> Tuple[Decimal, Decimal]:
        total_debit = sum(line['debit'] for line in self.lines)
        total_credit = sum(line['credit'] for line in self.lines)
        return total_debit, total_credit
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'date': self.date,
            'description': self.description,
            'lines': [
                {
                    'account_code': line['account_code'],
                    'debit': str(line['debit']),
                    'credit': str(line['credit'])
                }
                for line in self.lines
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'JournalEntry':
        lines = [
            {
                'account_code': line['account_code'],
                'debit': Decimal(line['debit']),
                'credit': Decimal(line['credit'])
            }
            for line in data['lines']
        ]
        return cls(
            data['id'],
            data['date'],
            data['description'],
            lines
        )

class AccountingSystem:
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.journal_entries: List[JournalEntry] = []
        self.next_entry_id = 1
        self._ensure_data_dir()
        self.load_data()
    
    def _ensure_data_dir(self) -> None:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            print(f"📁 Created data directory: {DATA_DIR}")
    
    def initialize_default_accounts(self) -> None:
        for code, data in DEFAULT_ACCOUNTS.items():
            self.accounts[code] = Account(
                code,
                data['name'],
                data['type'],
                data['normal_balance']
            )
        print(f"✅ Initialized {len(self.accounts)} default accounts")
    
    def add_account(self, code: str, name: str, account_type: str, normal_balance: str) -> bool:
        if code in self.accounts:
            print(f"❌ Account {code} already exists!")
            return False
        
        if account_type not in ACCOUNT_TYPES.values():
            print(f"❌ Invalid account type. Must be one of: {', '.join(ACCOUNT_TYPES.values())}")
            return False
        
        if normal_balance not in ['debit', 'credit']:
            print("❌ Normal balance must be 'debit' or 'credit'")
            return False
        
        self.accounts[code] = Account(code, name, account_type, normal_balance)
        self.save_data()
        print(f"✅ Account {code} - {name} added successfully!")
        return True
    
    def post_journal_entry(self, date: str, description: str, lines: List[Dict]) -> bool:
        for line in lines:
            if line['account_code'] not in self.accounts:
                print(f"❌ Account {line['account_code']} not found!")
                return False
        
        entry = JournalEntry(self.next_entry_id, date, description, lines)
        
        if not entry.validate():
            total_debit, total_credit = entry.get_totals()
            print(f"❌ Debits (${total_debit:,.2f}) do not equal Credits (${total_credit:,.2f})!")
            return False
        
        for line in lines:
            account = self.accounts[line['account_code']]
            if line['debit'] > 0:
                account.balance += line['debit']
            if line['credit'] > 0:
                account.balance -= line['credit']
        
        self.journal_entries.append(entry)
        self.next_entry_id += 1
        self.save_data()
        print(f"✅ Journal Entry #{entry.id} posted successfully!")
        return True
    
    def get_trial_balance(self) -> Tuple[List[Dict], Decimal, Decimal]:
        trial_balance = []
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        
        for code, account in sorted(self.accounts.items()):
            balance = account.balance
            if account.normal_balance == 'debit':
                debit = balance if balance > 0 else Decimal('0')
                credit = -balance if balance < 0 else Decimal('0')
            else:
                credit = balance if balance > 0 else Decimal('0')
                debit = -balance if balance < 0 else Decimal('0')
            
            if debit > 0 or credit > 0:
                trial_balance.append({
                    'code': code,
                    'name': account.name,
                    'type': account.type,
                    'debit': debit,
                    'credit': credit
                })
                total_debit += debit
                total_credit += credit
        
        return trial_balance, total_debit, total_credit
    
    def get_income_statement(self) -> Dict:
        income_accounts = []
        expense_accounts = []
        
        for code, account in self.accounts.items():
            if account.type == 'INCOME' and account.balance != 0:
                income_accounts.append((code, account.name, account.balance))
            elif account.type == 'EXPENSE' and account.balance != 0:
                expense_accounts.append((code, account.name, account.balance))
        
        total_revenue = sum(balance for _, _, balance in income_accounts)
        total_expenses = sum(balance for _, _, balance in expense_accounts)
        net_income = total_revenue - total_expenses
        
        return {
            'revenue': income_accounts,
            'expenses': expense_accounts,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': net_income
        }
    
    def get_balance_sheet(self) -> Dict:
        assets = []
        liabilities = []
        equity = []
        
        for code, account in self.accounts.items():
            if account.type == 'ASSET' and account.balance != 0:
                assets.append((code, account.name, account.balance))
            elif account.type == 'LIABILITY' and account.balance != 0:
                liabilities.append((code, account.name, account.balance))
            elif account.type == 'EQUITY' and account.balance != 0:
                equity.append((code, account.name, account.balance))
        
        total_assets = sum(balance for _, _, balance in assets)
        total_liabilities = sum(balance for _, _, balance in liabilities)
        total_equity = sum(balance for _, _, balance in equity)
        
        return {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity
        }
    
    def save_data(self) -> None:
        accounts_data = {
            code: account.to_dict()
            for code, account in self.accounts.items()
        }
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts_data, f, indent=2)
        
        entries_data = [entry.to_dict() for entry in self.journal_entries]
        with open(JOURNAL_FILE, 'w') as f:
            json.dump(entries_data, f, indent=2)
    
    def load_data(self) -> None:
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, 'r') as f:
                    accounts_data = json.load(f)
                    for code, data in accounts_data.items():
                        self.accounts[code] = Account.from_dict(data)
                print(f"✅ Loaded {len(self.accounts)} accounts")
            except Exception as e:
                print(f"⚠️ Error loading accounts: {e}")
                self.initialize_default_accounts()
        else:
            self.initialize_default_accounts()
        
        if os.path.exists(JOURNAL_FILE):
            try:
                with open(JOURNAL_FILE, 'r') as f:
                    entries_data = json.load(f)
                    for data in entries_data:
                        entry = JournalEntry.from_dict(data)
                        self.journal_entries.append(entry)
                        if entry.id >= self.next_entry_id:
                            self.next_entry_id = entry.id + 1
                print(f"✅ Loaded {len(self.journal_entries)} journal entries")
            except Exception as e:
                print(f"⚠️ Error loading journal entries: {e}")
    
    def print_accounts(self) -> None:
        print("\n" + "="*90)
        print("📊 CHART OF ACCOUNTS")
        print("="*90)
        print(f"{'Code':<8} {'Account Name':<35} {'Type':<12} {'Normal':<8} {'Balance':>20}")
        print("-"*90)
        for code, account in sorted(self.accounts.items()):
            print(f"{code:<8} {account.name[:35]:<35} {account.type:<12} {account.normal_balance:<8} ${account.balance:>19,.2f}")
        print("="*90)
    
    def print_trial_balance(self) -> None:
        trial_balance, total_debit, total_credit = self.get_trial_balance()
        
        print("\n" + "="*90)
        print("📋 TRIAL BALANCE")
        print("="*90)
        print(f"{'Code':<8} {'Account Name':<40} {'Type':<12} {'Debit':>18} {'Credit':>18}")
        print("-"*90)
        for item in trial_balance:
            print(f"{item['code']:<8} {item['name'][:40]:<40} {item['type']:<12} ${item['debit']:>17,.2f} ${item['credit']:>17,.2f}")
        print("-"*90)
        print(f"{'TOTAL':<8} {'':<40} {'':<12} ${total_debit:>17,.2f} ${total_credit:>17,.2f}")
        print("="*90)
        
        if total_debit == total_credit:
            print("✅ TRIAL BALANCE IS BALANCED!")
        else:
            print(f"❌ TRIAL BALANCE IS NOT BALANCED! Difference: ${abs(total_debit - total_credit):,.2f}")
    
    def print_income_statement(self) -> None:
        pnl = self.get_income_statement()
        
        print("\n" + "="*90)
        print("📈 INCOME STATEMENT (Profit & Loss)")
        print("="*90)
        print("\nREVENUE:")
        for code, name, balance in pnl['revenue']:
            print(f"  {code} {name[:35]:<35} ${balance:>17,.2f}")
        print("-"*90)
        print(f"{'Total Revenue':<50} ${pnl['total_revenue']:>17,.2f}")
        
        print("\nEXPENSES:")
        for code, name, balance in pnl['expenses']:
            print(f"  {code} {name[:35]:<35} ${balance:>17,.2f}")
        print("-"*90)
        print(f"{'Total Expenses':<50} ${pnl['total_expenses']:>17,.2f}")
        print("="*90)
        print(f"{'NET INCOME (Loss)':<50} ${pnl['net_income']:>17,.2f}")
        print("="*90)
    
    def print_balance_sheet(self) -> None:
        bs = self.get_balance_sheet()
        
        print("\n" + "="*90)
        print("📊 BALANCE SHEET")
        print("="*90)
        
        print("\nASSETS:")
        for code, name, balance in bs['assets']:
            print(f"  {code} {name[:35]:<35} ${balance:>17,.2f}")
        print("-"*90)
        print(f"{'Total Assets':<50} ${bs['total_assets']:>17,.2f}")
        
        print("\nLIABILITIES:")
        for code, name, balance in bs['liabilities']:
            print(f"  {code} {name[:35]:<35} ${balance:>17,.2f}")
        print("-"*90)
        print(f"{'Total Liabilities':<50} ${bs['total_liabilities']:>17,.2f}")
        
        print("\nEQUITY:")
        for code, name, balance in bs['equity']:
            print(f"  {code} {name[:35]:<35} ${balance:>17,.2f}")
        print("-"*90)
        print(f"{'Total Equity':<50} ${bs['total_equity']:>17,.2f}")
        print("="*90)
        print(f"{'TOTAL LIABILITIES + EQUITY':<50} ${bs['total_liabilities'] + bs['total_equity']:>17,.2f}")
        print("="*90)
        
        if abs(bs['total_assets'] - (bs['total_liabilities'] + bs['total_equity'])) < Decimal('0.01'):
            print("✅ BALANCE SHEET IS BALANCED!")
        else:
            print("❌ BALANCE SHEET IS NOT BALANCED!")
    
    def print_journal(self) -> None:
        if not self.journal_entries:
            print("\n📭 No journal entries yet.")
            return
        
        print("\n" + "="*90)
        print("📓 GENERAL JOURNAL")
        print("="*90)
        for entry in self.journal_entries:
            print(f"\nEntry #{entry.id} - {entry.date}")
            print(f"Description: {entry.description}")
            print(f"{'Account':<35} {'Debit':>18} {'Credit':>18}")
            print("-"*71)
            for line in entry.lines:
                account = self.accounts[line['account_code']]
                name = f"{line['account_code']} {account.name}"
                print(f"{name[:35]:<35} ${line['debit']:>17,.2f} ${line['credit']:>17,.2f}")
            print("-"*71)
            total_debit, total_credit = entry.get_totals()
            print(f"{'TOTAL':<35} ${total_debit:>17,.2f} ${total_credit:>17,.2f}")
        print("="*90)

# ============================================
# MAIN INTERFACE
# ============================================

def main():
    system = AccountingSystem()
    
    while True:
        print("\n" + "="*90)
        print(f"🏦 PROFESSIONAL ACCOUNTING SYSTEM v{VERSION}")
        print("="*90)
        print("\n📋 MAIN MENU")
        print("-"*90)
        print("1. 📊 View Chart of Accounts")
        print("2. ➕ Add New Account")
        print("3. 📓 Post Journal Entry")
        print("4. 📋 View Trial Balance")
        print("5. 📈 Income Statement (P&L)")
        print("6. 📊 Balance Sheet")
        print("7. 📓 View Journal Entries")
        print("8. 🔍 Account Balance")
        print("9. 🗑️ Reset All Data")
        print("10. 🚪 Exit")
        print("="*90)
        
        choice = input("\nEnter your choice (1-10): ").strip()
        
        if choice == "1":
            system.print_accounts()
        
        elif choice == "2":
            print("\n➕ ADD NEW ACCOUNT")
            code = input("Account Code (e.g., 1090): ").strip()
            if not code:
                print("❌ Account code is required!")
                continue
            
            name = input("Account Name: ").strip()
            if not name:
                print("❌ Account name is required!")
                continue
            
            print(f"\nAccount Types: {', '.join(ACCOUNT_TYPES.values())}")
            account_type = input("Account Type: ").strip().upper()
            
            normal_balance = input("Normal Balance (debit/credit): ").strip().lower()
            
            system.add_account(code, name, account_type, normal_balance)
        
        elif choice == "3":
            print("\n📓 POST JOURNAL ENTRY")
            print("-"*50)
            
            date = input("Date (YYYY-MM-DD) [Enter for today]: ").strip()
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            description = input("Description: ").strip()
            if not description:
                print("❌ Description is required!")
                continue
            
            lines = []
            while True:
                print(f"\nLine {len(lines) + 1}:")
                account_code = input("Account Code (or 'done' to finish): ").strip()
                if account_code.lower() == 'done':
                    break
                
                if account_code not in system.accounts:
                    print(f"❌ Account {account_code} not found!")
                    print("Available accounts:", ', '.join(list(system.accounts.keys())[:10]) + "...")
                    continue
                
                try:
                    debit = Decimal(input("Debit amount (0 if none): ").strip() or '0')
                    credit = Decimal(input("Credit amount (0 if none): ").strip() or '0')
                except InvalidOperation:
                    print("❌ Invalid amount!")
                    continue
                
                if debit > 0 and credit > 0:
                    print("❌ Cannot have both debit and credit on same line!")
                    continue
                if debit == 0 and credit == 0:
                    print("❌ Must have either debit or credit!")
                    continue
                
                lines.append({
                    'account_code': account_code,
                    'debit': debit,
                    'credit': credit
                })
                
                more = input("\nAdd another line? (y/n): ").strip().lower()
                if more != 'y':
                    break
            
            if lines:
                system.post_journal_entry(date, description, lines)
            else:
                print("❌ No lines entered!")
        
        elif choice == "4":
            system.print_trial_balance()
        
        elif choice == "5":
            system.print_income_statement()
        
        elif choice == "6":
            system.print_balance_sheet()
        
        elif choice == "7":
            system.print_journal()
        
        elif choice == "8":
            print("\n💰 ACCOUNT BALANCE")
            code = input("Enter account code: ").strip()
            if code in system.accounts:
                account = system.accounts[code]
                print(f"\n{account.code} - {account.name}")
                print(f"Type: {account.type}")
                print(f"Normal Balance: {account.normal_balance}")
                print(f"Current Balance: ${account.balance:,.2f}")
            else:
                print("❌ Account not found!")
        
        elif choice == "9":
            print("\n⚠️  WARNING: This will delete ALL data!")
            print("This action cannot be undone!")
            confirm = input("Type 'YES' to confirm: ").strip()
            if confirm == "YES":
                if os.path.exists(ACCOUNTS_FILE):
                    os.remove(ACCOUNTS_FILE)
                if os.path.exists(JOURNAL_FILE):
                    os.remove(JOURNAL_FILE)
                system.accounts = {}
                system.journal_entries = []
                system.next_entry_id = 1
                system.initialize_default_accounts()
                print("✅ All data has been reset!")
            else:
                print("❌ Operation cancelled.")
        
        elif choice == "10":
            print("\n👋 Goodbye!")
            sys.exit(0)
        
        else:
            print("❌ Invalid choice. Please enter 1-10.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        print("Please report this issue.")
        sys.exit(1)
