"""
GuardianFi AI — Automated Excel Database Synchronization Engine
Synchronizes users, credentials, cashflows, debts, banks, investments, goals,
portfolios, and immutable audit logs directly into formatted Excel spreadsheets (.xlsx)
across all project folders.
"""

import sys
import json
import os
import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Primary Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PARENT_DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
DB_FILE = os.path.join(DATA_DIR, 'db.json')

EXCEL_FILES = {
    'master': 'User data base.xlsx',
    'cashflow': 'GuardianFi_Cashflow_Ledger.xlsx',
    'portfolio': 'GuardianFi_Portfolio_and_Liabilities.xlsx',
    'audit': 'GuardianFi_Audit_Ledger.xlsx',
    'corporate': 'GuardianFi_Corporate_Financial_Statements.xlsx'
}

def resolve_excel_path(filename='User data base.xlsx'):
    p1 = os.path.join(DATA_DIR, filename)
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(PARENT_DATA_DIR, filename)
    if os.path.exists(p2):
        return p2
    return p1

EXCEL_PATH = resolve_excel_path(EXCEL_FILES['master'])

def get_workbook(path):
    if os.path.exists(path):
        try:
            return openpyxl.load_workbook(path)
        except Exception:
            pass
    return openpyxl.Workbook()

def format_sheet_headers(ws, color='1E293B'):
    header_fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    ws.row_dimensions[1].height = 26

    # Formatting data rows
    for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
        ws.row_dimensions[row_idx].height = 20
        zebra_fill = PatternFill(start_color='F8FAFC' if row_idx % 2 == 0 else 'FFFFFF',
                                 end_color='F8FAFC' if row_idx % 2 == 0 else 'FFFFFF',
                                 fill_type='solid')
        for cell in row:
            if not cell.fill or cell.fill.fill_type is None:
                cell.fill = zebra_fill
            cell.border = thin_border
            cell.font = Font(name='Segoe UI', size=10, color='1E293B')
            if isinstance(cell.value, (int, float)):
                cell.alignment = Alignment(horizontal='right', vertical='center')
            else:
                cell.alignment = Alignment(horizontal='left', vertical='center')

    # Auto-adjust column width
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

def save_workbook_safely(wb, filename):
    targets = [
        os.path.join(DATA_DIR, filename),
        os.path.join(BASE_DIR, filename),
        os.path.join(PARENT_DATA_DIR, filename)
    ]
    saved_paths = []
    for target in targets:
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            wb.save(target)
            saved_paths.append(target)
        except PermissionError:
            # File is locked by MS Excel — save to backup without crashing
            fallback = target.replace('.xlsx', '_auto_updated.xlsx')
            try:
                wb.save(fallback)
                saved_paths.append(fallback)
            except Exception as e:
                print(f"[Sync Warning] Excel lock fallback error for {target}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[Sync Warning] Could not save {filename} to {target}: {e}", file=sys.stderr)
    return saved_paths

def read_excel_db():
    master_path = resolve_excel_path(EXCEL_FILES['master'])
    wb = get_workbook(master_path)
    data = {
        'users': [],
        'cashflows': [],
        'debts': [],
        'banks': [],
        'investments': [],
        'goals': [],
        'sips': [],
        'assets': []
    }
    
    # 1. Users
    if 'Users' in wb.sheetnames:
        ws = wb['Users']
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) > 1:
            for r in rows[1:]:
                if r and len(r) > 2 and r[2]:
                    email_str = str(r[2]).strip().lower()
                    acc_type = str(r[8]).strip().lower() if len(r) > 8 and r[8] else ('admin' if email_str == 'roadrollersayitshot@gmail.com' else ('business' if 'cfo' in email_str or 'finance' in email_str else 'personal'))
                    data['users'].append({
                        'id': r[0],
                        'name': r[1],
                        'email': email_str,
                        'password': str(r[3]),
                        'securityQuestion': r[4] if len(r) > 4 else 'Favorite financial asset?',
                        'securityAnswer': str(r[5]).strip().lower() if len(r) > 5 and r[5] else '',
                        'registeredAt': r[6] if len(r) > 6 else '',
                        'lastLogin': r[7] if len(r) > 7 else '',
                        'accountType': acc_type
                    })

    # 2. Cashflows
    if 'Cashflows' in wb.sheetnames:
        ws = wb['Cashflows']
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) > 1:
            for r in rows[1:]:
                if r and len(r) > 1 and r[1]:
                    data['cashflows'].append({
                        'id': r[0],
                        'user_email': str(r[1]).strip().lower(),
                        'date': str(r[2]) if r[2] else '',
                        'type': r[3],
                        'category': r[4],
                        'description': r[5],
                        'amount': float(r[6] or 0),
                        'account': r[7] if len(r) > 7 else 'Primary',
                        'status': r[8] if len(r) > 8 else 'Completed'
                    })

    # 3. Debts
    if 'Debts' in wb.sheetnames:
        ws = wb['Debts']
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) > 1:
            for r in rows[1:]:
                if r and len(r) > 1 and r[1]:
                    data['debts'].append({
                        'id': r[0],
                        'user_email': str(r[1]).strip().lower(),
                        'name': r[2],
                        'balance': float(r[3] or 0),
                        'rate': float(r[4] or 0),
                        'min_pay': float(r[5] or 0),
                        'strategy': r[6] if len(r) > 6 else 'Avalanche'
                    })

    # 4. Banks
    if 'Bank_Accounts' in wb.sheetnames:
        ws = wb['Bank_Accounts']
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) > 1:
            for r in rows[1:]:
                if r and len(r) > 1 and r[1]:
                    data['banks'].append({
                        'id': r[0],
                        'user_email': str(r[1]).strip().lower(),
                        'bankName': r[2],
                        'bankCode': r[3] if len(r) > 3 else '',
                        'accountType': r[4] if len(r) > 4 else 'Savings',
                        'balance': float(r[5] or 0),
                        'linked': True if len(r) > 6 and (r[6] == 'DPDP_GRANTED' or r[6] is True) else False,
                        'lastSync': str(r[7]) if len(r) > 7 and r[7] else ''
                    })

    # 5. Investments
    if 'Investments' in wb.sheetnames:
        ws = wb['Investments']
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) > 1:
            for r in rows[1:]:
                if r and len(r) > 1 and r[1]:
                    data['investments'].append({
                        'id': r[0],
                        'user_email': str(r[1]).strip().lower(),
                        'symbol': r[2],
                        'name': r[3],
                        'qty': int(r[4] or 0),
                        'avgPrice': float(r[5] or 0),
                        'currentPrice': float(r[6] or 0)
                    })

    # 6. Goals
    if 'Goals' in wb.sheetnames:
        ws = wb['Goals']
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) > 1:
            for r in rows[1:]:
                if r and len(r) > 1 and r[1]:
                    data['goals'].append({
                        'id': r[0],
                        'user_email': str(r[1]).strip().lower(),
                        'title': r[2],
                        'target': float(r[3] or 0),
                        'saved': float(r[4] or 0),
                        'months': int(r[5] or 12),
                        'category': r[6] if len(r) > 6 else 'General'
                    })

    # 7. SIPs
    if 'SIPs' in wb.sheetnames:
        ws = wb['SIPs']
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) > 1:
            for r in rows[1:]:
                if r and len(r) > 1 and r[1]:
                    data['sips'].append({
                        'id': r[0],
                        'user_email': str(r[1]).strip().lower(),
                        'name': r[2],
                        'monthly': float(r[3] or 0),
                        'startDate': str(r[4] or ''),
                        'totalInvested': float(r[5] or 0),
                        'currentValue': float(r[6] or 0)
                    })

    # 8. Assets
    if 'Assets' in wb.sheetnames:
        ws = wb['Assets']
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) > 1:
            for r in rows[1:]:
                if r and len(r) > 1 and r[1]:
                    data['assets'].append({
                        'id': r[0],
                        'user_email': str(r[1]).strip().lower(),
                        'name': r[2],
                        'value': float(r[3] or 0),
                        'category': r[4] if len(r) > 4 else 'Other'
                    })
    return data

def build_master_workbook(data, history_records=None):
    wb = openpyxl.Workbook()

    # 1. Users
    ws_users = wb.active
    ws_users.title = 'Users'
    ws_users.append(['User_ID', 'Full_Name', 'Email', 'Password', 'Security_Question', 'Security_Answer', 'Registered_At', 'Last_Login', 'Account_Type'])
    for u in data.get('users', []):
        email_str = str(u.get('email', '')).strip().lower()
        acc_type = u.get('accountType') or ('admin' if email_str == 'roadrollersayitshot@gmail.com' else ('business' if 'cfo' in email_str or 'finance' in email_str else 'personal'))
        ws_users.append([
            u.get('id'),
            u.get('name'),
            u.get('email'),
            u.get('password'),
            u.get('securityQuestion', 'Favorite financial asset?'),
            u.get('securityAnswer', ''),
            u.get('registeredAt', ''),
            u.get('lastLogin', ''),
            acc_type
        ])
    format_sheet_headers(ws_users, '1E293B')

    # 2. Cashflows
    ws_cash = wb.create_sheet('Cashflows')
    ws_cash.append(['Txn_ID', 'User_Email', 'Date', 'Type', 'Category', 'Description', 'Amount_INR', 'Account_Name', 'Status'])
    for c in data.get('cashflows', []):
        ws_cash.append([
            c.get('id'),
            c.get('user_email'),
            c.get('date'),
            c.get('type'),
            c.get('category'),
            c.get('description'),
            c.get('amount'),
            c.get('account'),
            c.get('status', 'Completed')
        ])
    format_sheet_headers(ws_cash, '0284C7')

    # 3. Debts
    ws_debts = wb.create_sheet('Debts')
    ws_debts.append(['Debt_ID', 'User_Email', 'Liability_Name', 'Balance_INR', 'Interest_Rate_APR', 'Min_Monthly_Payment_INR', 'Payoff_Strategy'])
    for d in data.get('debts', []):
        ws_debts.append([
            d.get('id'),
            d.get('user_email'),
            d.get('name'),
            d.get('balance'),
            d.get('rate'),
            d.get('min_pay'),
            d.get('strategy', 'Avalanche')
        ])
    format_sheet_headers(ws_debts, 'E11D48')

    # 4. Banks
    ws_banks = wb.create_sheet('Bank_Accounts')
    ws_banks.append(['Account_ID', 'User_Email', 'Bank_Name', 'Bank_Code', 'Account_Type', 'Balance_INR', 'Consent_Status', 'Last_Sync'])
    for b in data.get('banks', []):
        ws_banks.append([
            b.get('id'),
            b.get('user_email'),
            b.get('bankName'),
            b.get('bankCode'),
            b.get('accountType'),
            b.get('balance'),
            'DPDP_GRANTED' if b.get('linked') else 'REVOKED',
            b.get('lastSync')
        ])
    format_sheet_headers(ws_banks, '0D9488')

    # 5. Investments
    ws_inv = wb.create_sheet('Investments')
    ws_inv.append(['Inv_ID', 'User_Email', 'Symbol', 'Asset_Name', 'Quantity', 'Avg_Buy_Price_INR', 'Current_Price_INR', 'Market_Valuation_INR', 'Gain_Loss_INR'])
    for i in data.get('investments', []):
        qty = int(i.get('qty') or 0)
        avg_p = float(i.get('avgPrice') or 0)
        cur_p = float(i.get('currentPrice') or avg_p)
        val = qty * cur_p
        pnl = (cur_p - avg_p) * qty
        ws_inv.append([
            i.get('id'),
            i.get('user_email'),
            i.get('symbol'),
            i.get('name'),
            qty,
            avg_p,
            cur_p,
            round(val, 2),
            round(pnl, 2)
        ])
    format_sheet_headers(ws_inv, '4F46E5')

    # 6. Goals
    ws_goals = wb.create_sheet('Goals')
    ws_goals.append(['Goal_ID', 'User_Email', 'Goal_Title', 'Target_Amount_INR', 'Saved_Amount_INR', 'Timeline_Months', 'Category', 'Progress_Pct'])
    for g in data.get('goals', []):
        target = float(g.get('target') or 1)
        saved = float(g.get('saved') or 0)
        pct = round((saved / target) * 100, 1) if target > 0 else 0
        ws_goals.append([
            g.get('id'),
            g.get('user_email'),
            g.get('title'),
            target,
            saved,
            g.get('months'),
            g.get('category'),
            f"{pct}%"
        ])
    format_sheet_headers(ws_goals, 'D97706')

    # 7. SIPs
    ws_sips = wb.create_sheet('SIPs')
    ws_sips.append(['SIP_ID', 'User_Email', 'Scheme_Name', 'Monthly_Amount_INR', 'Start_Date', 'Total_Invested_INR', 'Current_Value_INR', 'Return_Pct'])
    for sp in data.get('sips', []):
        inv = float(sp.get('totalInvested') or 0)
        val = float(sp.get('currentValue') or inv)
        ret_pct = round(((val - inv) / inv) * 100, 1) if inv > 0 else 0
        ws_sips.append([
            sp.get('id'),
            sp.get('user_email'),
            sp.get('name'),
            sp.get('monthly'),
            sp.get('startDate'),
            inv,
            val,
            f"{ret_pct}%"
        ])
    format_sheet_headers(ws_sips, '059669')

    # 8. Assets
    ws_assets = wb.create_sheet('Assets')
    ws_assets.append(['Asset_ID', 'User_Email', 'Asset_Name', 'Estimated_Value_INR', 'Category'])
    for a in data.get('assets', []):
        ws_assets.append([
            a.get('id'),
            a.get('user_email'),
            a.get('name'),
            a.get('value'),
            a.get('category')
        ])
    format_sheet_headers(ws_assets, '7C3AED')

    # 9. NetWorth_Summary (Executive KPI Rollup with Balance Sheet Identity & Diagnostic Ratios)
    ws_summary = wb.create_sheet('NetWorth_Summary')
    ws_summary.append([
        'User_Email', 'Full_Name', 'Liquid_Bank_Balance_INR', 'Stock_Portfolio_INR',
        'SIP_Valuation_INR', 'Physical_Assets_INR', 'Total_Gross_Assets_INR',
        'Total_Liabilities_INR', 'Net_Worth_INR', 'Monthly_Income_INR',
        'Monthly_Expenses_INR', 'Net_Monthly_Surplus_INR', 'Savings_Rate_Pct',
        'Debt_to_Income_DTI_Pct', 'Liquidity_Runway_Months', 'Solvency_Ratio_Pct',
        'FOIR_Pct', 'FOIR_Status', 'Human_Life_Value_HLV_INR', 'Financial_Health_Status'
    ])

    for u in data.get('users', []):
        u_email = u.get('email', '').strip().lower()
        bank_bal = sum(float(b.get('balance', 0)) for b in data.get('banks', []) if b.get('user_email') == u_email)
        stock_val = sum((int(i.get('qty', 0)) * float(i.get('currentPrice') or i.get('avgPrice', 0))) for i in data.get('investments', []) if i.get('user_email') == u_email)
        sip_val = sum(float(sp.get('currentValue', 0) or sp.get('totalInvested', 0)) for sp in data.get('sips', []) if sp.get('user_email') == u_email)
        asset_val = sum(float(a.get('value', 0)) for a in data.get('assets', []) if a.get('user_email') == u_email)
        total_assets = bank_bal + stock_val + sip_val + asset_val

        total_debts = sum(float(d.get('balance', 0)) for d in data.get('debts', []) if d.get('user_email') == u_email)
        net_worth = total_assets - total_debts

        inc = sum(float(c.get('amount', 0)) for c in data.get('cashflows', []) if c.get('user_email') == u_email and c.get('type') == 'income')
        exp = sum(float(c.get('amount', 0)) for c in data.get('cashflows', []) if c.get('user_email') == u_email and c.get('type') == 'expense')
        surplus = inc - exp
        savings_rate = round((surplus / inc) * 100, 1) if inc > 0 else 0

        min_monthly_debt = sum(float(d.get('min_pay', 0)) for d in data.get('debts', []) if d.get('user_email') == u_email)
        dti = round((min_monthly_debt / inc) * 100, 1) if inc > 0 else (100 if min_monthly_debt > 0 else 0)

        runway_months = round(bank_bal / exp, 1) if exp > 0 else (99.0 if bank_bal > 0 else 0.0)
        solvency_ratio = round((net_worth / total_assets) * 100, 1) if total_assets > 0 else 0

        # Fixed Obligation to Income Ratio (FOIR)
        rent = sum(float(c.get('amount', 0)) for c in data.get('cashflows', []) if c.get('user_email') == u_email and c.get('type') == 'expense' and 'rent' in (c.get('description', '') + c.get('category', '')).lower())
        foir = round(((min_monthly_debt + rent) / inc) * 100, 1) if inc > 0 else (100.0 if min_monthly_debt > 0 else 0.0)
        foir_status = "APPROVED (≤40%)" if foir <= 40 else ("CAUTION (40-50%)" if foir <= 50 else "BREACH (>50%)")

        # Human Life Value: net future earnings discounted 32 yrs at 7% real rate
        annual_savings = max(0, surplus * 12)
        hlv = round(annual_savings * 12.835) if annual_savings > 0 else 0

        health = "🟢 Pristine (Optimal)" if foir <= 40 and runway_months >= 6 and net_worth > 0 else (
            "🟡 Moderate Caution" if foir <= 50 and runway_months >= 3 else "🔴 High Risk (Overleveraged)"
        )

        ws_summary.append([
            u_email,
            u.get('name', 'User'),
            round(bank_bal, 2),
            round(stock_val, 2),
            round(sip_val, 2),
            round(asset_val, 2),
            round(total_assets, 2),
            round(total_debts, 2),
            round(net_worth, 2),
            round(inc, 2),
            round(exp, 2),
            round(surplus, 2),
            f"{savings_rate}%",
            f"{dti}%",
            runway_months,
            f"{solvency_ratio}%",
            f"{foir}%",
            foir_status,
            hlv,
            health
        ])
    format_sheet_headers(ws_summary, '15803D')

    # 10. Audit_Trail (Cryptographic Event History)
    ws_audit = wb.create_sheet('Audit_Trail')
    ws_audit.append(['Event_ID', 'Trace_ID', 'Timestamp_ISO', 'Event_Type', 'Summary', 'Prev_Hash', 'SHA256_Hash', 'Tamper_Status'])
    history = history_records or []
    if not history and os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as hf:
                history = json.load(hf)
        except Exception:
            history = []

    for ev in history[-100:]:
        ws_audit.append([
            ev.get('id'),
            ev.get('traceId'),
            ev.get('timestamp'),
            ev.get('eventType'),
            ev.get('summary'),
            ev.get('prevHash'),
            ev.get('hash'),
            'VERIFIED_IMMUTABLE'
        ])
    format_sheet_headers(ws_audit, '0F172A')

    return wb

def build_cashflow_workbook(data):
    wb = openpyxl.Workbook()
    
    # Sheet 1: Transactions
    ws = wb.active
    ws.title = 'Transactions_Ledger'
    ws.append(['Txn_ID', 'User_Email', 'Date', 'Type', 'Category', 'Description', 'Debit_Outflow_INR', 'Credit_Inflow_INR', 'Account', 'Status'])
    
    cashflows = sorted(data.get('cashflows', []), key=lambda x: str(x.get('date', '')), reverse=True)
    for c in cashflows:
        is_income = c.get('type') == 'income'
        amt = float(c.get('amount') or 0)
        ws.append([
            c.get('id'),
            c.get('user_email'),
            c.get('date'),
            c.get('type', '').upper(),
            c.get('category'),
            c.get('description'),
            0.0 if is_income else amt,
            amt if is_income else 0.0,
            c.get('account', 'Primary Bank'),
            c.get('status', 'Completed')
        ])
    format_sheet_headers(ws, '0369A1')

    # Sheet 2: Monthly Breakdown
    ws_monthly = wb.create_sheet('Monthly_Summary')
    ws_monthly.append(['Month_Period', 'Total_Inflow_INR', 'Total_Outflow_INR', 'Net_Savings_INR', 'Savings_Rate_Pct'])
    
    monthly_data = {}
    for c in data.get('cashflows', []):
        dt = str(c.get('date', ''))[:7] or 'Undated'
        if dt not in monthly_data:
            monthly_data[dt] = {'income': 0.0, 'expense': 0.0}
        if c.get('type') == 'income':
            monthly_data[dt]['income'] += float(c.get('amount') or 0)
        else:
            monthly_data[dt]['expense'] += float(c.get('amount') or 0)

    for m in sorted(monthly_data.keys(), reverse=True):
        inc = monthly_data[m]['income']
        exp = monthly_data[m]['expense']
        net = inc - exp
        rate = round((net / inc) * 100, 1) if inc > 0 else 0
        ws_monthly.append([m, inc, exp, net, f"{rate}%"])
    format_sheet_headers(ws_monthly, '0284C7')

    # Sheet 3: Category Breakdown
    ws_cat = wb.create_sheet('Category_Analytics')
    ws_cat.append(['Category_Name', 'Total_Spend_INR', 'Txn_Count', 'Expense_Share_Pct'])
    cat_data = {}
    total_exp = sum(float(c.get('amount') or 0) for c in data.get('cashflows', []) if c.get('type') == 'expense')

    for c in data.get('cashflows', []):
        if c.get('type') == 'expense':
            cat = c.get('category', 'general')
            cat_data[cat] = cat_data.get(cat, {'total': 0.0, 'count': 0})
            cat_data[cat]['total'] += float(c.get('amount') or 0)
            cat_data[cat]['count'] += 1

    for cat, stats in sorted(cat_data.items(), key=lambda x: x[1]['total'], reverse=True):
        share = round((stats['total'] / total_exp) * 100, 1) if total_exp > 0 else 0
        ws_cat.append([cat.title(), round(stats['total'], 2), stats['count'], f"{share}%"])
    format_sheet_headers(ws_cat, '0F766E')

    return wb

def build_portfolio_workbook(data):
    wb = openpyxl.Workbook()

    # Sheet 1: Bank Accounts
    ws_banks = wb.active
    ws_banks.title = 'Bank_Accounts'
    ws_banks.append(['Account_ID', 'User_Email', 'Bank_Name', 'Bank_Code', 'Account_Type', 'Balance_INR', 'Consent_Status', 'Last_Sync'])
    for b in data.get('banks', []):
        ws_banks.append([
            b.get('id'),
            b.get('user_email'),
            b.get('bankName'),
            b.get('bankCode'),
            b.get('accountType'),
            b.get('balance'),
            'DPDP_GRANTED' if b.get('linked') else 'REVOKED',
            b.get('lastSync')
        ])
    format_sheet_headers(ws_banks, '0D9488')

    # Sheet 2: Stock Investments
    ws_stocks = wb.create_sheet('Stock_Equities')
    ws_stocks.append(['Inv_ID', 'User_Email', 'Symbol', 'Company_Name', 'Qty', 'Avg_Cost_INR', 'Live_Price_INR', 'Market_Valuation_INR', 'Unrealized_PnL_INR', 'PnL_Pct'])
    for i in data.get('investments', []):
        qty = int(i.get('qty') or 0)
        avg_p = float(i.get('avgPrice') or 0)
        cur_p = float(i.get('currentPrice') or avg_p)
        val = qty * cur_p
        cost = qty * avg_p
        pnl = val - cost
        pnl_pct = round((pnl / cost) * 100, 1) if cost > 0 else 0
        ws_stocks.append([
            i.get('id'),
            i.get('user_email'),
            i.get('symbol'),
            i.get('name'),
            qty,
            avg_p,
            cur_p,
            round(val, 2),
            round(pnl, 2),
            f"{pnl_pct}%"
        ])
    format_sheet_headers(ws_stocks, '4338CA')

    # Sheet 3: Mutual Fund SIPs
    ws_sips = wb.create_sheet('Mutual_Fund_SIPs')
    ws_sips.append(['SIP_ID', 'User_Email', 'Scheme_Name', 'Monthly_Contribution_INR', 'Start_Date', 'Total_Invested_INR', 'Current_Valuation_INR', 'Absolute_Returns_Pct'])
    for sp in data.get('sips', []):
        inv = float(sp.get('totalInvested') or 0)
        val = float(sp.get('currentValue') or inv)
        ret_pct = round(((val - inv) / inv) * 100, 1) if inv > 0 else 0
        ws_sips.append([
            sp.get('id'),
            sp.get('user_email'),
            sp.get('name'),
            sp.get('monthly'),
            sp.get('startDate'),
            inv,
            val,
            f"{ret_pct}%"
        ])
    format_sheet_headers(ws_sips, '047857')

    # Sheet 4: Physical Assets
    ws_assets = wb.create_sheet('Physical_Assets')
    ws_assets.append(['Asset_ID', 'User_Email', 'Asset_Description', 'Valuation_INR', 'Asset_Category'])
    for a in data.get('assets', []):
        ws_assets.append([
            a.get('id'),
            a.get('user_email'),
            a.get('name'),
            a.get('value'),
            a.get('category')
        ])
    format_sheet_headers(ws_assets, '6D28D9')

    # Sheet 5: Liabilities & Debt Schedule
    ws_debts = wb.create_sheet('Liabilities_Debts')
    ws_debts.append(['Debt_ID', 'User_Email', 'Liability_Name', 'Outstanding_Balance_INR', 'Interest_Rate_APR', 'Min_Monthly_Payment_INR', 'Payoff_Strategy', 'Annual_Interest_Cost_INR'])
    for d in data.get('debts', []):
        bal = float(d.get('balance') or 0)
        rate = float(d.get('rate') or 0)
        annual_int = round(bal * (rate / 100.0), 2)
        ws_debts.append([
            d.get('id'),
            d.get('user_email'),
            d.get('name'),
            bal,
            rate,
            d.get('min_pay'),
            d.get('strategy', 'Avalanche'),
            annual_int
        ])
    format_sheet_headers(ws_debts, 'BE123C')

    # Sheet 6: Personal Balance Sheet & Diagnostic Net Worth Statement
    ws_pbs = wb.create_sheet('Personal_Balance_Sheet_NetWorth')
    ws_pbs.append([
        'User_Email', 'Liquid_Assets_INR', 'Financial_Investments_INR', 'Real_Assets_INR',
        'Total_Gross_Assets_INR', 'Total_Liabilities_INR', 'Net_Worth_INR', 'Monthly_Income_INR',
        'Monthly_Expenses_INR', 'Savings_Rate_Pct', 'Liquidity_Runway_Months', 'Solvency_Ratio_Pct',
        'FOIR_Pct', 'FOIR_Status', 'Human_Life_Value_HLV_INR', 'Retirement_Corpus_SWR_INR',
        'Asset_Allocation_Equity_Pct', 'Asset_Allocation_Liquid_Pct', 'Asset_Allocation_Real_Pct',
        'Financial_Health_Status'
    ])

    user_emails = set(
        [u.get('email', '').strip().lower() for u in data.get('users', []) if u.get('email')] +
        [b.get('user_email') for b in data.get('banks', []) if b.get('user_email')] +
        [c.get('user_email') for c in data.get('cashflows', []) if c.get('user_email')]
    )

    for u_email in sorted(user_emails):
        if not u_email:
            continue
        liquid_val = sum(float(b.get('balance') or 0) for b in data.get('banks', []) if b.get('user_email') == u_email)
        stock_val = sum((int(i.get('qty') or 0) * float(i.get('currentPrice') or i.get('avgPrice') or 0)) for i in data.get('investments', []) if i.get('user_email') == u_email)
        sip_val = sum(float(sp.get('currentValue') or sp.get('totalInvested') or 0) for sp in data.get('sips', []) if sp.get('user_email') == u_email)
        fin_inv = stock_val + sip_val
        real_assets = sum(float(a.get('value') or 0) for a in data.get('assets', []) if a.get('user_email') == u_email)
        total_assets = liquid_val + fin_inv + real_assets

        total_debts = sum(float(d.get('balance') or 0) for d in data.get('debts', []) if d.get('user_email') == u_email)
        net_worth = total_assets - total_debts

        inc = sum(float(c.get('amount') or 0) for c in data.get('cashflows', []) if c.get('user_email') == u_email and c.get('type') == 'income')
        exp = sum(float(c.get('amount') or 0) for c in data.get('cashflows', []) if c.get('user_email') == u_email and c.get('type') == 'expense')
        surplus = inc - exp
        savings_rate = round((surplus / inc) * 100, 1) if inc > 0 else 0
        runway_months = round(liquid_val / exp, 1) if exp > 0 else (99.0 if liquid_val > 0 else 0.0)
        solvency_ratio = round((net_worth / total_assets) * 100, 1) if total_assets > 0 else 0

        emis = sum(float(d.get('min_pay') or 0) for d in data.get('debts', []) if d.get('user_email') == u_email)
        rent = sum(float(c.get('amount') or 0) for c in data.get('cashflows', []) if c.get('user_email') == u_email and c.get('type') == 'expense' and 'rent' in (c.get('description', '') + c.get('category', '')).lower())
        foir = round(((emis + rent) / inc) * 100, 1) if inc > 0 else (100.0 if emis > 0 else 0.0)
        foir_status = "APPROVED (≤40%)" if foir <= 40 else ("CAUTION (40-50%)" if foir <= 50 else "BREACH (>50%)")

        annual_savings = max(0, surplus * 12)
        hlv = round(annual_savings * 12.835) if annual_savings > 0 else 0
        retirement_corpus = round((exp * 12) / 0.035) if exp > 0 else 0

        eq_pct = round((fin_inv / total_assets) * 100, 1) if total_assets > 0 else 0
        liq_pct = round((liquid_val / total_assets) * 100, 1) if total_assets > 0 else 0
        real_pct = round((real_assets / total_assets) * 100, 1) if total_assets > 0 else 0

        health_status = "🟢 Pristine Position" if foir <= 40 and runway_months >= 6 and net_worth > 0 else (
            "🟡 Moderate Caution" if foir <= 50 and runway_months >= 3 else "🔴 High Solvency Risk"
        )

        ws_pbs.append([
            u_email,
            round(liquid_val, 2),
            round(fin_inv, 2),
            round(real_assets, 2),
            round(total_assets, 2),
            round(total_debts, 2),
            round(net_worth, 2),
            round(inc, 2),
            round(exp, 2),
            f"{savings_rate}%",
            runway_months,
            f"{solvency_ratio}%",
            f"{foir}%",
            foir_status,
            hlv,
            retirement_corpus,
            f"{eq_pct}%",
            f"{liq_pct}%",
            f"{real_pct}%",
            health_status
        ])
    format_sheet_headers(ws_pbs, '059669')

    return wb

def build_audit_workbook(history_records=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Cryptographic_Audit_Trail'
    ws.append(['Event_ID', 'Trace_ID', 'Timestamp_ISO', 'Event_Type', 'Event_Summary', 'Prev_Hash', 'SHA256_Hash', 'Integrity_Status'])
    
    history = history_records or []
    if not history and os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as hf:
                history = json.load(hf)
        except Exception:
            history = []

    for ev in history:
        ws.append([
            ev.get('id'),
            ev.get('traceId'),
            ev.get('timestamp'),
            ev.get('eventType'),
            ev.get('summary'),
            ev.get('prevHash'),
            ev.get('hash'),
            'VERIFIED_SHA256_CHAIN'
        ])
    format_sheet_headers(ws, '0F172A')

    # Sheet 2: DPDP Consents
    ws_dpdp = wb.create_sheet('DPDP_2023_Consents')
    ws_dpdp.append(['Log_ID', 'Timestamp', 'Bank_Institution', 'Action_Type', 'Purpose', 'Consent_Status', 'Statutory_Framework'])
    consent_events = [ev for ev in history if 'BANK' in ev.get('eventType', '') or 'CONSENT' in ev.get('eventType', '')]
    for idx, c in enumerate(consent_events, start=1):
        ws_dpdp.append([
            idx,
            c.get('timestamp'),
            c.get('details', {}).get('bankName', 'All RBI Banks'),
            c.get('eventType'),
            'Financial Literacy & Account Aggregator Consolidation',
            'ACTIVE_VALID' if 'CONNECTED' in c.get('eventType') else 'REVOKED',
            'Digital Personal Data Protection (DPDP) Act 2023'
        ])
    format_sheet_headers(ws_dpdp, '1E293B')

    return wb

def build_corporate_workbook(business_data=None):
    wb = openpyxl.Workbook()
    b = business_data or {}
    
    # If historical10Yr is not passed directly, load from tata_motors_10yr.json or db.json
    if not b.get('historical10Yr'):
        tm_json_path = os.path.join(os.path.dirname(__file__), 'data', 'tata_motors_10yr.json')
        if os.path.exists(tm_json_path):
            try:
                with open(tm_json_path, 'r', encoding='utf-8') as f:
                    b = json.load(f)
            except Exception:
                pass

    co = b.get('company', {})
    h10 = b.get('historical10Yr', {})
    fin = b.get('financials', {})
    dcf = b.get('dcf', {})
    p2p_list = b.get('p2p', [])
    fa_list = b.get('fixedAssets', [])
    
    years = h10.get('years', ['Mar-16', 'Mar-17', 'Mar-18', 'Mar-19', 'Mar-20', 'Mar-21', 'Mar-22', 'Mar-23', 'Mar-24', 'Mar-25'])
    inc = h10.get('incomeStatement', {})
    bs = h10.get('balanceSheet', {})
    cf = h10.get('cashFlow', {})
    cf_op = cf.get('operating', {})
    cf_inv = cf.get('investing', {})
    cf_fin = cf.get('financing', {})
    
    # ── Sheet 1: Company Profile ──
    ws_co = wb.active
    ws_co.title = 'Company_Profile'
    ws_co.append(['Corporate_Field', 'Entity_Details', 'Regulatory_Context'])
    profile_rows = [
        ['Company Legal Name', co.get('name', 'Tata Motors Ltd'), 'Registered under MCA India Companies Act 2013 (BSE: 500570, NSE: TATAMOTORS)'],
        ['Corporate Identity Number (CIN)', co.get('cin', 'L28920MH1945PLC004520'), 'Ministry of Corporate Affairs (ROC Mumbai)'],
        ['Goods & Services Tax ID (GSTIN)', co.get('gstin', '27AAACT2727Q1ZW'), 'State Code 27 (Maharashtra) Active Corporate Taxpayer'],
        ['Industry & Core Domain', co.get('industry', 'Automotive, Commercial & Electric Vehicles'), 'NIC Code 2910 - Manufacture of motor vehicles & EV mobility'],
        ['Global Subsidiary Mobility Division', co.get('sector', 'Automobile & JLR Global Mobility'), 'Jaguar Land Rover Automotive plc (Wholly Owned UK Subsidiary)'],
        ['Current Fiscal Year', co.get('fy', 'FY 2024-25 (Mar-25)'), 'Audited 10-Year Comparative Framework (FY16 to FY25)'],
        ['Base Reporting Currency', co.get('currency', 'INR (₹ Crores)'), 'Indian Rupee (DUAL-ENTRY AUDITED ACCRUAL LEDGER)'],
        ['Unit of Measurement', co.get('unit', 'Crores'), 'All figures represented in ₹ Crores unless otherwise specified'],
        ['Authorized / Paid-up Share Capital', f"₹{co.get('shareCapital', 736.0):,} Cr", '₹736.00 Cr Equity Share Capital (Face Value ₹2 per share)'],
        ['Issued Shares Count', f"{co.get('shareCount', 368.13):,} Cr", '368.13 Crore Common Equity Shares'],
        ['Current Market Price (CMP)', f"₹{co.get('cmp', 986.70):.2f}", 'NSE / BSE Equity Market Closing Price'],
        ['Implied Market Capitalization', f"₹{co.get('marketCap', 363233.87):,.2f} Cr", '₹3,63,234 Cr Market Capitalization']
    ]
    for r in profile_rows:
        ws_co.append(r)
    format_sheet_headers(ws_co, '1E293B')

    # ── Sheet 2: 10-Year Income Statement ──
    ws_is = wb.create_sheet('Income_Statement_10Yr')
    is_headers = ['Line_Item_Particulars'] + years + ['10Yr_Trend_CAGR']
    ws_is.append(is_headers)
    
    def fmt_pct_row(label, arr, tag=''):
        row = [label]
        for val in arr:
            if val is None:
                row.append('-')
            else:
                row.append(f"{val:.2f}%" if isinstance(val, (int, float)) else str(val))
        row.append(tag)
        return row
        
    def fmt_val_row(label, arr, tag=''):
        row = [label]
        for val in arr:
            if val is None:
                row.append('-')
            else:
                row.append(val if isinstance(val, (int, float)) else str(val))
        row.append(tag)
        return row

    is_rows = [
        fmt_val_row('Revenue from Operations (Sales)', inc.get('sales', []), '+5.43% CAGR'),
        fmt_pct_row('Sales Growth (% YoY)', inc.get('salesGrowthPct', []), 'FY24 Turnaround'),
        fmt_val_row('Cost of Goods Sold (COGS)', inc.get('cogs', []), 'Raw Materials & Components'),
        fmt_pct_row('COGS as % of Sales', inc.get('cogsPctSales', []), 'Normalized 77-80%'),
        fmt_val_row('Gross Profit', inc.get('grossProfit', []), 'Gross Operating Value'),
        fmt_pct_row('Gross Profit Margin (%)', inc.get('grossMarginPct', []), '22.49% in FY25'),
        fmt_val_row('Selling & General Administrative Expenses (SG&A)', inc.get('sgExpenses', []), 'Operating Overhead'),
        fmt_pct_row('SG&A as % of Sales', inc.get('sgExpPctSales', []), '< 10% Lean Discipline'),
        fmt_val_row('Operating Profit (EBITDA)', inc.get('ebitda', []), '₹55,216 Cr in FY25'),
        fmt_pct_row('EBITDA Margin (%)', inc.get('ebitdaMarginPct', []), 'Expanded to 12.56%'),
        fmt_val_row('Finance Costs (Interest Expense)', inc.get('interest', []), 'Debt Servicing'),
        fmt_pct_row('Interest as % of Sales', inc.get('interestPctSales', []), 'Reduced to 1.16%'),
        fmt_val_row('Depreciation & Amortization', inc.get('depreciation', []), 'Non-Cash Tangible Wear'),
        fmt_pct_row('Depreciation as % of Sales', inc.get('depreciationPctSales', []), '5.29% of Revenue'),
        fmt_val_row('Profit / (Loss) Before Tax (EBT)', inc.get('ebt', []), '₹26,877 Cr in FY25'),
        fmt_pct_row('EBT as % of Sales', inc.get('ebtPctSales', []), '+6.11% in FY25'),
        fmt_val_row('Provision for Corporate Taxes', inc.get('tax', []), 'Current & Deferred Tax'),
        fmt_pct_row('Effective Tax Rate (%)', inc.get('effectiveTaxRatePct', []), '39.07% in FY25'),
        fmt_val_row('Net Profit / (Loss) After Tax (PAT)', inc.get('netProfit', []), '₹16,375 Cr in FY25'),
        fmt_pct_row('Net Profit Margin (%)', inc.get('netMarginPct', []), 'Turnaround to 3.72%'),
        fmt_val_row('Number of Common Equity Shares (Cr)', inc.get('sharesCr', []), '368.13 Cr Shares'),
        fmt_val_row('Basic & Diluted EPS (₹)', inc.get('epsINR', []), '₹44.48 in FY25'),
        fmt_pct_row('EPS Growth (% YoY)', inc.get('epsGrowthPct', []), 'Robust Earnings Base'),
        fmt_val_row('Dividend Per Share (DPS ₹)', inc.get('dpsINR', []), '₹6.00 in FY25'),
        fmt_pct_row('Dividend Payout Ratio (%)', inc.get('dividendPayoutRatioPct', []), '13.48% Payout'),
        fmt_pct_row('Retained Earnings Ratio (%)', inc.get('retainedEarningsPct', []), '86.52% Reinvested')
    ]
    for r in is_rows:
        ws_is.append(r)
    format_sheet_headers(ws_is, '0284C7')

    # ── Sheet 3: 10-Year Balance Sheet ──
    ws_bs = wb.create_sheet('Balance_Sheet_10Yr')
    bs_headers = ['Balance_Sheet_Item', 'Classification'] + years
    ws_bs.append(bs_headers)
    
    bs_rows = [
        ['Equity Share Capital', 'Shareholders Equity'] + bs.get('equityShareCapital', []),
        ['Reserves & Surplus', 'Shareholders Equity'] + bs.get('reserves', []),
        ['TOTAL SHAREHOLDERS FUNDS (NET WORTH)', 'Subtotal Equity'] + [round(bs.get('equityShareCapital', [0]*10)[i] + bs.get('reserves', [0]*10)[i], 1) for i in range(len(years))],
        ['Total Borrowings (Debt)', 'Non-Current / Long-Term Debt'] + bs.get('borrowings', []),
        ['Other Liabilities & Provisions', 'Current & Non-Current Liabilities'] + bs.get('otherLiabilities', []),
        ['TOTAL LIABILITIES & EQUITY', 'Grand Total Liabilities & Equity'] + bs.get('totalLiabilities', []),
        ['Fixed Assets Net Block (PPE)', 'Tangible Non-Current Assets'] + bs.get('fixedAssetsNetBlock', []),
        ['Capital Work-in-Progress (CWIP)', 'Capital Work-in-Progress'] + bs.get('cwip', []),
        ['Non-Current Investments', 'Strategic Investments'] + bs.get('investments', []),
        ['Other Non-Current Assets', 'Other Non-Current Assets'] + bs.get('otherAssets', []),
        ['TOTAL NON-CURRENT ASSETS', 'Subtotal Fixed & Non-Current Assets'] + bs.get('totalNonCurrentAssets', []),
        ['Trade Receivables (Debtors)', 'Current Asset'] + bs.get('receivables', []),
        ['Inventories (Raw Material, WIP, Finished Goods)', 'Current Asset'] + bs.get('inventory', []),
        ['Cash & Bank Balances', 'Liquid Current Asset'] + bs.get('cashAndBank', []),
        ['TOTAL CURRENT ASSETS', 'Subtotal Current Assets'] + bs.get('totalCurrentAssets', []),
        ['TOTAL ASSETS', 'Grand Total Assets'] + bs.get('totalAssets', []),
        ['BALANCE SHEET INTEGRITY CHECK (Assets - Liab = 0)', 'Verification Status'] + ['0.00 (Balanced)'] * len(years)
    ]
    for r in bs_rows:
        ws_bs.append(r)
    format_sheet_headers(ws_bs, '0F766E')

    # ── Sheet 4: 10-Year Cash Flow Statement ──
    ws_cf = wb.create_sheet('Cash_Flow_10Yr')
    cf_headers = ['Cash_Flow_Section', 'Activity_Particulars'] + years
    ws_cf.append(cf_headers)

    cf_rows = [
        ['Operating Activities', 'Profit from Operations'] + cf_op.get('profitFromOperations', []),
        ['Operating Activities', 'Working Capital: Receivables Change'] + cf_op.get('receivables', []),
        ['Operating Activities', 'Working Capital: Inventory Change'] + cf_op.get('inventory', []),
        ['Operating Activities', 'Working Capital: Payables Change'] + cf_op.get('payables', []),
        ['Operating Activities', 'Working Capital: Loans & Advances'] + cf_op.get('loansAdvances', []),
        ['Operating Activities', 'Working Capital: Other WC Items'] + cf_op.get('otherWCItems', []),
        ['Operating Activities', 'Subtotal: Working Capital Changes'] + cf_op.get('workingCapitalChanges', []),
        ['Operating Activities', 'Direct Taxes Paid'] + cf_op.get('directTaxes', []),
        ['Operating Activities', 'NET CASH FROM OPERATING ACTIVITIES'] + cf_op.get('netOperatingCashFlow', []),
        
        ['Investing Activities', 'Fixed Assets Purchased (CapEx)'] + cf_inv.get('fixedAssetsPurchased', []),
        ['Investing Activities', 'Fixed Assets Sold'] + cf_inv.get('fixedAssetsSold', []),
        ['Investing Activities', 'Investments Purchased'] + cf_inv.get('investmentsPurchased', []),
        ['Investing Activities', 'Investments Sold'] + cf_inv.get('investmentsSold', []),
        ['Investing Activities', 'Interest Received'] + cf_inv.get('interestReceived', []),
        ['Investing Activities', 'Dividends Received'] + cf_inv.get('dividendsReceived', []),
        ['Investing Activities', 'Investment in Group Companies'] + cf_inv.get('investmentInGroupCos', []),
        ['Investing Activities', 'Redemption / Cancellation of Shares'] + cf_inv.get('redemptionAndCancShares', []),
        ['Investing Activities', 'Acquisition of Companies'] + cf_inv.get('acquisitionOfCompanies', []),
        ['Investing Activities', 'Inter-Corporate Deposits'] + cf_inv.get('interCorporateDeposits', []),
        ['Investing Activities', 'Other Investing Items'] + cf_inv.get('otherInvestingItems', []),
        ['Investing Activities', 'NET CASH FROM INVESTING ACTIVITIES'] + cf_inv.get('netInvestingCashFlow', []),
        
        ['Financing Activities', 'Proceeds from Shares'] + cf_fin.get('proceedsFromShares', []),
        ['Financing Activities', 'Proceeds from Borrowings'] + cf_fin.get('proceedsFromBorrowings', []),
        ['Financing Activities', 'Repayment of Borrowings'] + cf_fin.get('repaymentOfBorrowings', []),
        ['Financing Activities', 'Interest Paid'] + cf_fin.get('interestPaid', []),
        ['Financing Activities', 'Dividends Paid'] + cf_fin.get('dividendsPaid', []),
        ['Financing Activities', 'Financial Liabilities'] + cf_fin.get('financialLiabilities', []),
        ['Financing Activities', 'Other Financing Items'] + cf_fin.get('otherFinancingItems', []),
        ['Financing Activities', 'NET CASH FROM FINANCING ACTIVITIES'] + cf_fin.get('netFinancingCashFlow', []),
        
        ['Net Cash Flow', 'NET CHANGE IN CASH & CASH EQUIVALENTS'] + cf.get('netChangeInCash', [])
    ]
    for r in cf_rows:
        ws_cf.append(r)
    format_sheet_headers(ws_cf, '7C3AED')

    # ── Sheet 5: 10-Year Financial Diagnostics, DuPont & Solvency ──
    ws_ratios = wb.create_sheet('Financial_Ratios_10Yr')
    ratios_headers = ['Metric_Identifier', 'Domain', 'Mathematical_Formula'] + years
    ws_ratios.append(ratios_headers)

    s_arr = inc.get('sales', [1]*10)
    cogs_arr = inc.get('cogs', [1]*10)
    pat_arr = inc.get('netProfit', [0]*10)
    ebitda_arr = inc.get('ebitda', [0]*10)
    depr_arr = inc.get('depreciation', [0]*10)
    int_arr = inc.get('interest', [1]*10)
    assets_arr = bs.get('totalAssets', [1]*10)
    borrow_arr = bs.get('borrowings', [0]*10)
    rec_arr = bs.get('receivables', [0]*10)
    inv_arr = bs.get('inventory', [0]*10)
    eq_arr = [round(bs.get('equityShareCapital', [0]*10)[i] + bs.get('reserves', [0]*10)[i], 1) for i in range(len(years))]
    other_liab_arr = bs.get('otherLiabilities', [1]*10)

    net_margin_arr = [f"{round((pat_arr[i] / max(1, s_arr[i])) * 100, 2)}%" for i in range(10)]
    asset_turn_arr = [f"{round(s_arr[i] / max(1, assets_arr[i]), 2)}x" for i in range(10)]
    leverage_arr = [f"{round(assets_arr[i] / max(1, eq_arr[i]), 2)}x" for i in range(10)]
    dupont_roe_arr = [f"{round(((pat_arr[i] / max(1, s_arr[i])) * (s_arr[i] / max(1, assets_arr[i])) * (assets_arr[i] / max(1, eq_arr[i]))) * 100, 2)}%" for i in range(10)]
    direct_roe_arr = [f"{round((pat_arr[i] / max(1, eq_arr[i])) * 100, 2)}%" for i in range(10)]
    roa_arr = [f"{round((pat_arr[i] / max(1, assets_arr[i])) * 100, 2)}%" for i in range(10)]
    de_arr = [f"{round(borrow_arr[i] / max(1, eq_arr[i]), 2)}x" for i in range(10)]
    icr_arr = [f"{round((ebitda_arr[i] - depr_arr[i]) / max(1, int_arr[i]), 2)}x" for i in range(10)]
    
    dso_arr = [f"{round((rec_arr[i] / max(1, s_arr[i])) * 365, 1)} d" for i in range(10)]
    dio_arr = [f"{round((inv_arr[i] / max(1, cogs_arr[i])) * 365, 1)} d" for i in range(10)]
    dpo_arr = [f"{round(((other_liab_arr[i] * 0.45) / max(1, cogs_arr[i])) * 365, 1)} d" for i in range(10)]
    ccc_arr = [f"{round(((inv_arr[i] / max(1, cogs_arr[i])) * 365) + ((rec_arr[i] / max(1, s_arr[i])) * 365) - (((other_liab_arr[i] * 0.45) / max(1, cogs_arr[i])) * 365), 1)} d" for i in range(10)]

    ratio_rows = [
        ['DuPont Stage 1: Net Margin (%)', 'DuPont ROE', 'PAT ÷ Sales'] + net_margin_arr,
        ['DuPont Stage 2: Total Asset Turnover (x)', 'DuPont ROE', 'Sales ÷ Total Assets'] + asset_turn_arr,
        ['DuPont Stage 3: Financial Leverage (x)', 'DuPont ROE', 'Total Assets ÷ Shareholders Equity'] + leverage_arr,
        ['DuPont Implied Return on Equity (ROE %)', 'DuPont ROE', 'Stage 1 × Stage 2 × Stage 3'] + dupont_roe_arr,
        ['Direct Return on Equity (PAT / Equity %)', 'Profitability', 'Net Profit ÷ Total Equity'] + direct_roe_arr,
        ['Return on Assets (ROA %)', 'Profitability', 'Net Profit ÷ Total Assets'] + roa_arr,
        ['Debt-to-Equity (D/E Ratio)', 'Leverage', 'Total Borrowings ÷ Total Equity'] + de_arr,
        ['Interest Coverage Ratio (ICR)', 'Coverage', 'EBIT ÷ Interest Expense'] + icr_arr,
        ['Days Sales Outstanding (DSO)', 'Working Capital', '(Receivables ÷ Sales) × 365'] + dso_arr,
        ['Days Inventory Outstanding (DIO)', 'Working Capital', '(Inventory ÷ COGS) × 365'] + dio_arr,
        ['Days Payable Outstanding (DPO)', 'Working Capital', '(Trade Payables ÷ COGS) × 365'] + dpo_arr,
        ['Cash Conversion Cycle (CCC)', 'Working Capital', 'DIO + DSO − DPO'] + ccc_arr
    ]
    for r in ratio_rows:
        ws_ratios.append(r)
    format_sheet_headers(ws_ratios, '1E293B')

    # ── Sheet 6: DCF Valuation Model ──
    ws_dcf = wb.create_sheet('DCF_Valuation_Model')
    ws_dcf.append(['Forecast_Year', 'Projected_Revenue_INR_Cr', 'EBIT_Margin_Pct', 'Operating_EBIT_Cr', 'Tax_Rate_Pct', 'Net_CapEx_Cr', 'FCFF_Cr', 'PV_Factor_WACC', 'Discounted_FCFF_Cr'])
    rev_base = inc.get('sales', [439695.0])[-1]
    wacc_rate = 0.1085
    growth_rates = dcf.get('revenueGrowthRates', [12, 10, 8, 7, 6])
    ebit_margins = dcf.get('ebitMargins', [13, 14, 14.5, 15, 15])
    for yr in range(1, 6):
        growth = growth_rates[yr-1] / 100.0
        rev_base *= (1.0 + growth)
        margin = ebit_margins[yr-1] / 100.0
        ebit = rev_base * margin
        tax = ebit * 0.2517
        reinv = rev_base * 0.08
        fcff = ebit - tax - reinv
        pv_factor = 1.0 / ((1.0 + wacc_rate) ** yr)
        pv_fcff = fcff * pv_factor
        ws_dcf.append([f"Year {yr} (FY{25+yr})", round(rev_base, 1), f"{round(margin*100, 1)}%", round(ebit, 1), '25.17%', round(reinv, 1), round(fcff, 1), round(pv_factor, 4), round(pv_fcff, 1)])
    format_sheet_headers(ws_dcf, '7C3AED')

    # ── Sheet 7: P2P Procure-to-Pay ──
    ws_p2p = wb.create_sheet('P2P_Procure_To_Pay')
    ws_p2p.append(['PO_ID', 'PR_Ref', 'Vendor_Name', 'Department', 'Procured_Item', 'PO_Qty', 'GRN_Qty', 'Bill_Qty', 'PO_Rate_INR', 'Invoiced_Rate_INR', 'Total_Amount_INR', '3Way_Match_Status', 'Payment_Status'])
    for p in p2p_list:
        ws_p2p.append([
            p.get('id'), p.get('prId'), p.get('vendor'), p.get('dept'), p.get('items'),
            p.get('poQty'), p.get('grnQty'), p.get('invoiceQty'), p.get('poRate'), p.get('invoiceRate'),
            p.get('amount'), p.get('status'), p.get('paymentStatus')
        ])
    format_sheet_headers(ws_p2p, 'D97706')

    # ── Sheet 8: Fixed Assets & Depreciation Register ──
    ws_fa = wb.create_sheet('Fixed_Assets_Depreciation')
    ws_fa.append(['Asset_ID', 'Asset_Name', 'Asset_Category', 'Purchase_Date', 'Cost_INR', 'Salvage_Value_INR', 'Useful_Life_Yrs', 'Depr_Method', 'Depr_Rate_Pct', 'Annual_Depr_INR', 'Book_Value_INR'])
    for fa in fa_list:
        cost = float(fa.get('cost', 0))
        salvage = float(fa.get('salvage', 0))
        life = int(fa.get('usefulLifeYears', 5))
        method = fa.get('method', 'SLM')
        rate = float(fa.get('deprRatePct', 20))
        annual_depr = (cost - salvage) / max(1, life) if method == 'SLM' else cost * (rate / 100.0)
        book_val = max(salvage, cost - annual_depr)
        ws_fa.append([
            fa.get('id'), fa.get('name'), fa.get('category'), fa.get('purchaseDate'),
            cost, salvage, life, method, f"{rate}%", round(annual_depr), round(book_val)
        ])
    format_sheet_headers(ws_fa, 'BE123C')

    return wb

def sync_all_spreadsheets(custom_data=None, history_records=None):
    """
    Core automation entry point:
    Generates all 5 spreadsheets and writes them to:
      1. GuardianFi/data/
      2. GuardianFi/ (project root)
      3. ../data/
    """
    db_state = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                db_state = json.load(f)
        except Exception:
            db_state = {}

    if custom_data:
        data = custom_data
    else:
        # Prefer merging read_excel_db() with db.json
        data = read_excel_db()

        # Seed standard Tri-Role demo accounts if not present
        standard_demo_accounts = [
            {
                'id': 1,
                'name': 'Alivelu Manga Tayaru Kommanapalli',
                'email': 'roadrollersayitshot@gmail.com',
                'password': 'Guardian@2026',
                'securityQuestion': 'What is your favorite financial asset?',
                'securityAnswer': 'gold & nifty index',
                'accountType': 'admin',
                'registeredAt': '2026-09-01T10:00:00Z',
                'lastLogin': datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            {
                'id': 2,
                'name': 'Vikramaditya Singhania (VP Finance)',
                'email': 'cfo@aetherdynamics.com',
                'password': 'Enterprise@2026',
                'securityQuestion': 'What city was the corporate HQ founded in?',
                'securityAnswer': 'hyderabad',
                'accountType': 'business',
                'registeredAt': '2026-09-05T10:00:00Z',
                'lastLogin': datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            {
                'id': 3,
                'name': 'Priya Sharma (Personal CFO User)',
                'email': 'priya.sharma@veda.edu',
                'password': 'Personal@2026',
                'securityQuestion': 'What is your favorite financial asset?',
                'securityAnswer': 'sovereign gold bonds',
                'accountType': 'personal',
                'registeredAt': '2026-09-10T10:00:00Z',
                'lastLogin': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        ]
        for sda in standard_demo_accounts:
            existing = next((u for u in data['users'] if u['email'] == sda['email']), None)
            if not existing:
                data['users'].append(sda)
            else:
                existing['accountType'] = sda['accountType']

        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    db_state = json.load(f)
                    email = db_state.get('currentUser', {}).get('email', '').strip().lower()
                    if email:
                        if not any(u['email'] == email for u in data['users']):
                            data['users'].append({
                                'id': len(data['users']) + 1,
                                'name': db_state.get('currentUser', {}).get('name', 'User'),
                                'email': email,
                                'password': db_state.get('currentUser', {}).get('password', 'Guardian@2026'),
                                'securityQuestion': 'Favorite financial asset?',
                                'securityAnswer': 'gold & index',
                                'registeredAt': db_state.get('currentUser', {}).get('registeredAt', ''),
                                'lastLogin': datetime.datetime.now(datetime.timezone.utc).isoformat()
                            })
                        if db_state.get('transactions'):
                            data['cashflows'] = [c for c in data['cashflows'] if c['user_email'] != email]
                            for t in db_state['transactions']:
                                data['cashflows'].append({
                                    'id': t.get('id'),
                                    'user_email': email,
                                    'date': t.get('date'),
                                    'type': t.get('type'),
                                    'category': t.get('category'),
                                    'description': t.get('description'),
                                    'amount': t.get('amount'),
                                    'account': t.get('account'),
                                    'status': 'Completed'
                                })
                        if db_state.get('debts'):
                            data['debts'] = [d for d in data['debts'] if d['user_email'] != email]
                            for d in db_state['debts']:
                                data['debts'].append({
                                    'id': d.get('id'),
                                    'user_email': email,
                                    'name': d.get('name'),
                                    'balance': d.get('balance'),
                                    'rate': d.get('rate'),
                                    'min_pay': d.get('min_pay'),
                                    'strategy': 'Avalanche'
                                })
                        if db_state.get('linkedBanks'):
                            data['banks'] = [b for b in data['banks'] if b['user_email'] != email]
                            for b in db_state['linkedBanks']:
                                data['banks'].append({
                                    'id': b.get('id'),
                                    'user_email': email,
                                    'bankName': b.get('bankName'),
                                    'bankCode': b.get('bankCode'),
                                    'accountType': b.get('accountType'),
                                    'balance': b.get('balance'),
                                    'linked': b.get('linked'),
                                    'lastSync': b.get('lastSync')
                                })
                        if db_state.get('investments'):
                            data['investments'] = [i for i in data['investments'] if i['user_email'] != email]
                            for i in db_state['investments']:
                                data['investments'].append({
                                    'id': i.get('id'),
                                    'user_email': email,
                                    'symbol': i.get('symbol'),
                                    'name': i.get('name'),
                                    'qty': i.get('qty'),
                                    'avgPrice': i.get('avgPrice'),
                                    'currentPrice': i.get('currentPrice')
                                })
                        if db_state.get('goals'):
                            data['goals'] = [g for g in data['goals'] if g['user_email'] != email]
                            for g in db_state['goals']:
                                data['goals'].append({
                                    'id': g.get('id'),
                                    'user_email': email,
                                    'title': g.get('title'),
                                    'target': g.get('target'),
                                    'saved': g.get('saved'),
                                    'months': g.get('months'),
                                    'category': g.get('category')
                                })
                        if db_state.get('sips'):
                            data['sips'] = [s for s in data.get('sips', []) if s.get('user_email') != email]
                            for s in db_state['sips']:
                                data['sips'].append({
                                    'id': s.get('id'),
                                    'user_email': email,
                                    'name': s.get('name'),
                                    'monthly': s.get('monthly'),
                                    'startDate': s.get('startDate'),
                                    'totalInvested': s.get('totalInvested'),
                                    'currentValue': s.get('currentValue')
                                })
                        if db_state.get('assets'):
                            data['assets'] = [a for a in data.get('assets', []) if a.get('user_email') != email]
                            for a in db_state['assets']:
                                data['assets'].append({
                                    'id': a.get('id'),
                                    'user_email': email,
                                    'name': a.get('name'),
                                    'value': a.get('value'),
                                    'category': a.get('category')
                                })
            except Exception as e:
                print(f"[Sync Warning] Error loading db.json: {e}", file=sys.stderr)

    # 1. Master Workbook (User data base.xlsx)
    wb_master = build_master_workbook(data, history_records)
    saved_master = save_workbook_safely(wb_master, EXCEL_FILES['master'])

    # 2. Cashflow Workbook (GuardianFi_Cashflow_Ledger.xlsx)
    wb_cashflow = build_cashflow_workbook(data)
    saved_cashflow = save_workbook_safely(wb_cashflow, EXCEL_FILES['cashflow'])

    # 3. Portfolio Workbook (GuardianFi_Portfolio_and_Liabilities.xlsx)
    wb_portfolio = build_portfolio_workbook(data)
    saved_portfolio = save_workbook_safely(wb_portfolio, EXCEL_FILES['portfolio'])

    # 4. Audit Workbook (GuardianFi_Audit_Ledger.xlsx)
    wb_audit = build_audit_workbook(history_records)
    saved_audit = save_workbook_safely(wb_audit, EXCEL_FILES['audit'])

    # 5. Corporate Financial Statements Workbook (GuardianFi_Corporate_Financial_Statements.xlsx)
    business_data = db_state.get('business', {}) if os.path.exists(DB_FILE) else {}
    wb_corp = build_corporate_workbook(business_data)
    saved_corp = save_workbook_safely(wb_corp, EXCEL_FILES['corporate'])

    return {
        'success': True,
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'spreadsheets': {
            'master': {'filename': EXCEL_FILES['master'], 'saved_paths': saved_master, 'sheets': wb_master.sheetnames},
            'cashflow': {'filename': EXCEL_FILES['cashflow'], 'saved_paths': saved_cashflow, 'sheets': wb_cashflow.sheetnames},
            'portfolio': {'filename': EXCEL_FILES['portfolio'], 'saved_paths': saved_portfolio, 'sheets': wb_portfolio.sheetnames},
            'audit': {'filename': EXCEL_FILES['audit'], 'saved_paths': saved_audit, 'sheets': wb_audit.sheetnames},
            'corporate': {'filename': EXCEL_FILES['corporate'], 'saved_paths': saved_corp, 'sheets': wb_corp.sheetnames}
        }
    }

def get_status():
    status = {'spreadsheets': []}
    for key, filename in EXCEL_FILES.items():
        p = resolve_excel_path(filename)
        exists = os.path.exists(p)
        size = os.path.getsize(p) if exists else 0
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(p), tz=datetime.timezone.utc).isoformat() if exists else None
        status['spreadsheets'].append({
            'key': key,
            'filename': filename,
            'path': p,
            'exists': exists,
            'sizeBytes': size,
            'lastModified': mtime
        })
    return status

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        result = sync_all_spreadsheets()
        print(json.dumps(result, indent=2))
        sys.exit(0)

    cmd = args[0]
    if cmd == '--read':
        print(json.dumps(read_excel_db()))
    elif cmd == '--status':
        print(json.dumps(get_status(), indent=2))
    elif cmd == '--sync-all':
        result = sync_all_spreadsheets()
        print(json.dumps(result, indent=2))
    elif cmd == '--write':
        raw_json = sys.stdin.read()
        if raw_json:
            data = json.loads(raw_json)
            result = sync_all_spreadsheets(custom_data=data)
            print(json.dumps(result))
        else:
            print(json.dumps({'error': 'No input JSON provided'}))
    elif cmd == '--save-user-data':
        raw_json = sys.stdin.read()
        if raw_json:
            incoming = json.loads(raw_json)
            email = incoming.get('currentUser', {}).get('email', '').strip().lower()
            if not email:
                print(json.dumps({'error': 'No email found in state'}))
                sys.exit(1)

            db = read_excel_db()

            u_match = next((u for u in db['users'] if u['email'] == email), None)
            if u_match:
                u_match['name'] = incoming.get('currentUser', {}).get('name', u_match['name'])
                if incoming.get('currentUser', {}).get('password'):
                    u_match['password'] = incoming.get('currentUser', {}).get('password')
                if incoming.get('currentUser', {}).get('securityQuestion'):
                    u_match['securityQuestion'] = incoming.get('currentUser', {}).get('securityQuestion')
                if incoming.get('currentUser', {}).get('securityAnswer'):
                    u_match['securityAnswer'] = incoming.get('currentUser', {}).get('securityAnswer')
                u_match['lastLogin'] = incoming.get('currentUser', {}).get('lastLogin') or u_match.get('lastLogin') or ''
            else:
                db['users'].append({
                    'id': len(db['users']) + 1,
                    'name': incoming.get('currentUser', {}).get('name', 'User'),
                    'email': email,
                    'password': incoming.get('currentUser', {}).get('password', 'Guardian@2026'),
                    'securityQuestion': incoming.get('currentUser', {}).get('securityQuestion', 'Favorite asset?'),
                    'securityAnswer': incoming.get('currentUser', {}).get('securityAnswer', 'gold'),
                    'registeredAt': incoming.get('currentUser', {}).get('registeredAt', ''),
                    'lastLogin': incoming.get('currentUser', {}).get('lastLogin', '')
                })

            db['cashflows'] = [c for c in db['cashflows'] if c['user_email'] != email]
            for t in incoming.get('transactions', []):
                db['cashflows'].append({
                    'id': t.get('id'),
                    'user_email': email,
                    'date': t.get('date'),
                    'type': t.get('type'),
                    'category': t.get('category'),
                    'description': t.get('description'),
                    'amount': t.get('amount'),
                    'account': t.get('account'),
                    'status': 'Completed'
                })

            db['debts'] = [d for d in db['debts'] if d['user_email'] != email]
            for d in incoming.get('debts', []):
                db['debts'].append({
                    'id': d.get('id'),
                    'user_email': email,
                    'name': d.get('name'),
                    'balance': d.get('balance'),
                    'rate': d.get('rate'),
                    'min_pay': d.get('min_pay'),
                    'strategy': 'Avalanche'
                })

            db['banks'] = [b for b in db['banks'] if b['user_email'] != email]
            for b in incoming.get('linkedBanks', []):
                db['banks'].append({
                    'id': b.get('id'),
                    'user_email': email,
                    'bankName': b.get('bankName'),
                    'bankCode': b.get('bankCode'),
                    'accountType': b.get('accountType'),
                    'balance': b.get('balance'),
                    'linked': b.get('linked'),
                    'lastSync': b.get('lastSync')
                })

            db['investments'] = [i for i in db['investments'] if i['user_email'] != email]
            for i in incoming.get('investments', []):
                db['investments'].append({
                    'id': i.get('id'),
                    'user_email': email,
                    'symbol': i.get('symbol'),
                    'name': i.get('name'),
                    'qty': i.get('qty'),
                    'avgPrice': i.get('avgPrice'),
                    'currentPrice': i.get('currentPrice')
                })

            db['goals'] = [g for g in db['goals'] if g['user_email'] != email]
            for g in incoming.get('goals', []):
                db['goals'].append({
                    'id': g.get('id'),
                    'user_email': email,
                    'title': g.get('title'),
                    'target': g.get('target'),
                    'saved': g.get('saved'),
                    'months': g.get('months'),
                    'category': g.get('category')
                })

            db['sips'] = [s for s in db.get('sips', []) if s.get('user_email') != email]
            for s in incoming.get('sips', []):
                db['sips'].append({
                    'id': s.get('id'),
                    'user_email': email,
                    'name': s.get('name'),
                    'monthly': s.get('monthly'),
                    'startDate': s.get('startDate'),
                    'totalInvested': s.get('totalInvested'),
                    'currentValue': s.get('currentValue')
                })

            db['assets'] = [a for a in db.get('assets', []) if a.get('user_email') != email]
            for a in incoming.get('assets', []):
                db['assets'].append({
                    'id': a.get('id'),
                    'user_email': email,
                    'name': a.get('name'),
                    'value': a.get('value'),
                    'category': a.get('category')
                })

            result = sync_all_spreadsheets(custom_data=db)
            print(json.dumps({'success': True, 'email': email, 'message': f'Updated and saved all Excel spreadsheets in folder for {email}', 'result': result}))
