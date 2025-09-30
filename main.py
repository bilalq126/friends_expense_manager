import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Fixed list of friends
FRIENDS = ["Bilal Qadeer", "Habib Khan", "Abdur Rehman", "Rehan Umer"]

@st.cache_data(ttl=30)  # Cache for 30 seconds to avoid too many API calls
def load_expenses():
    """Load expenses from Sheety API"""
    try:
        sheety_url = st.secrets["sheety"]["get_url"]
        response = requests.get(sheety_url)
        
        if response.status_code == 200:
            data = response.json()
            expenses = data.get("expenses", [])
            if expenses:
                return pd.DataFrame(expenses)
        
        return pd.DataFrame(columns=['date', 'amount', 'payers', 'contributions', 'present', 'description'])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=['date', 'amount', 'payers', 'contributions', 'present', 'description'])

def save_expense(amount, payers_contributions, present, description):
    """Save expense to Sheety API"""
    try:
        sheety_url = st.secrets["sheety"]["post_url"]
        
        expense_data = {
            "expense": {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "payers": ', '.join([f"{name}: {contrib}" for name, contrib in payers_contributions.items() if contrib > 0]),
                "contributions": str(payers_contributions),
                "present": ', '.join(present),
                "description": description
            }
        }
        
        response = requests.post(sheety_url, json=expense_data)
        
        if response.status_code != 200:
            st.error(f"Failed to save expense: {response.text}")
            return False
        return True
    except Exception as e:
        st.error(f"Error saving expense: {e}")
        return False

def calculate_balances():
    """Calculate net balances for each friend"""
    expenses_df = load_expenses()
    balances = {friend: 0.0 for friend in FRIENDS}
    
    for _, expense in expenses_df.iterrows():
        amount = float(expense['amount'])
        contributions = eval(expense['contributions'])
        present = expense['present'].split(', ')
        
        # Calculate split amount per person
        split_per_person = amount / len(present)
        
        # Update balances
        for friend in present:
            balances[friend] -= split_per_person  # Everyone owes their share
            
        for friend, contribution in contributions.items():
            if contribution > 0:
                balances[friend] += contribution  # Add what they paid
    
    return balances

def calculate_settlements(balances):
    """Calculate who owes whom"""
    creditors = {name: bal for name, bal in balances.items() if bal > 0}
    debtors = {name: abs(bal) for name, bal in balances.items() if bal < 0}
    
    settlements = []
    
    for debtor, debt_amount in debtors.items():
        remaining_debt = debt_amount
        for creditor, credit_amount in creditors.items():
            if remaining_debt > 0 and credit_amount > 0:
                settlement_amount = min(remaining_debt, credit_amount)
                settlements.append(f"{debtor} owes {creditor}: PKR {settlement_amount:.2f}")
                creditors[creditor] -= settlement_amount
                remaining_debt -= settlement_amount
    
    return settlements

def main():
    st.title("Friends Expense Manager 💰")
    st.markdown("**For: Bilal Qadeer, Habib Khan, Abdur Rehman, Rehan Umer**")
    
    # Sidebar for adding expenses
    st.sidebar.header("Add New Expense")
    
    with st.sidebar:
        description = st.text_input("Description", placeholder="e.g., Dinner at restaurant")
        total_amount = st.number_input("Total Amount (PKR)", min_value=0.0, step=1.0)
        
        st.subheader("Who paid?")
        payers_contributions = {}
        total_paid = 0.0
        
        for friend in FRIENDS:
            contribution = st.number_input(f"{friend} paid (PKR)", min_value=0.0, step=1.0, key=f"pay_{friend}")
            payers_contributions[friend] = contribution
            total_paid += contribution
        
        st.write(f"Total paid: PKR {total_paid:.2f}")
        
        if total_paid != total_amount and total_amount > 0:
            st.warning(f"Total paid ({total_paid:.2f}) doesn't match total amount ({total_amount:.2f})")
        
        st.subheader("Who was present?")
        present = st.multiselect("Select who was present", FRIENDS, default=FRIENDS)
        
        if st.button("Add Expense", disabled=(total_amount == 0 or len(present) == 0 or total_paid != total_amount)):
            if save_expense(total_amount, payers_contributions, present, description):
                st.success("Expense added successfully!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Failed to add expense!")
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Current Balances")
        balances = calculate_balances()
        
        for friend, balance in balances.items():
            if balance > 0:
                st.success(f"**{friend}**: +PKR {balance:.2f} (to receive)")
            elif balance < 0:
                st.error(f"**{friend}**: PKR {abs(balance):.2f} (to pay)")
            else:
                st.info(f"**{friend}**: PKR 0.00 (settled)")
    
    with col2:
        st.header("Settlements Needed")
        settlements = calculate_settlements(balances)
        
        if settlements:
            for settlement in settlements:
                st.write(f"• {settlement}")
        else:
            st.success("All settled! 🎉")
    
    # Expense history
    st.header("Expense History")
    expenses_df = load_expenses()
    
    if not expenses_df.empty:
        # Display expenses in reverse chronological order
        expenses_df_display = expenses_df.copy()
        expenses_df_display['amount'] = expenses_df_display['amount'].apply(lambda x: f"PKR {float(x):.2f}")
        st.dataframe(expenses_df_display.iloc[::-1], use_container_width=True)
        
        # Download CSV button
        csv_data = expenses_df.to_csv(index=False)
        st.download_button(
            label="Download Expenses CSV",
            data=csv_data,
            file_name="friends_expenses.csv",
            mime="text/csv"
        )
        
        # Show Sheety/Google Sheets link
        sheet_url = st.secrets["sheety"].get("sheet_url", "")
        if sheet_url:
            st.markdown(f"📊 [View Live Google Sheet]({sheet_url})")
    else:
        st.info("No expenses recorded yet. Add your first expense using the sidebar!")

if __name__ == "__main__":
    main()
        tab_add, tab_edit, tab_admin = st.tabs(["Add Expense", "Edit Expense", "Admin Actions"])
        # ...existing code for Add and Edit tabs...
        with tab_add:
            # ...existing code...
            description = st.text_input("Description", placeholder="e.g., Dinner at restaurant")
            total_amount = st.number_input("Total Amount (PKR)", min_value=0.0, step=1.0, key="add_total_amount")
            st.subheader("Who paid?")
            payers_contributions = {}
            total_paid = 0.0
            for friend in FRIENDS:
                contribution = st.number_input(f"{friend} paid (PKR)", min_value=0.0, step=1.0, key=f"add_pay_{friend}")
                payers_contributions[friend] = contribution
                total_paid += contribution
            st.write(f"Total paid: PKR {total_paid:.2f}")
            if total_paid != total_amount and total_amount > 0:
                st.warning(f"Total paid ({total_paid:.2f}) doesn't match total amount ({total_amount:.2f})")
            st.subheader("Who was present?")
            present = st.multiselect("Select who was present", FRIENDS, default=FRIENDS, key="add_present")
            if st.button("Add Expense", key="add_expense_btn", disabled=(total_amount == 0 or len(present) == 0 or total_paid != total_amount)):
                save_expense(total_amount, payers_contributions, present, description)
                st.success("Expense added successfully!")
                st.rerun()
        with tab_edit:
            st.subheader("Select Expense to Edit")
            if not expenses_df.empty:
                expense_options = [f"{row['Date']} | {row['Description']}" for _, row in expenses_df.iterrows()]
                selected_idx = st.selectbox("Choose an expense", options=range(len(expenses_df)), format_func=lambda i: expense_options[i], key="edit_select")
                selected_expense = expenses_df.iloc[selected_idx]
                edit_description = st.text_input("Description", value=selected_expense['Description'], key="edit_description")
                edit_total_amount = st.number_input("Total Amount (PKR)", min_value=0.0, step=1.0, value=float(selected_expense['Amount']), key="edit_total_amount")
                st.subheader("Who paid?")
                # Parse contributions
                try:
                    edit_contributions = eval(selected_expense['Contributions'])
                except:
                    edit_contributions = {friend: 0.0 for friend in FRIENDS}
                edit_payers_contributions = {}
                edit_total_paid = 0.0
                for friend in FRIENDS:
                    val = float(edit_contributions.get(friend, 0.0))
                    edit_payers_contributions[friend] = st.number_input(f"{friend} paid (PKR)", min_value=0.0, step=1.0, value=val, key=f"edit_pay_{friend}")
                    edit_total_paid += edit_payers_contributions[friend]
                st.write(f"Total paid: PKR {edit_total_paid:.2f}")
                if edit_total_paid != edit_total_amount and edit_total_amount > 0:
                    st.warning(f"Total paid ({edit_total_paid:.2f}) doesn't match total amount ({edit_total_amount:.2f})")
                st.subheader("Who was present?")
                present_list = selected_expense['Present'].split(', ')
                edit_present = st.multiselect("Select who was present", FRIENDS, default=present_list, key="edit_present")
                if st.button("Save Changes", key="edit_expense_btn", disabled=(edit_total_amount == 0 or len(edit_present) == 0 or edit_total_paid != edit_total_amount)):
                    success = edit_expense(selected_idx, edit_total_amount, edit_payers_contributions, edit_present, edit_description)
                    if success:
                        st.success("Expense updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update expense.")
            else:
                st.info("No expenses to edit.")
        with tab_admin:
            st.subheader("Admin Actions")
            st.markdown("**Password required for these actions**")
            admin_password = st.text_input("Enter admin password", type="password", key="admin_password")
            st.write("")
            # Remove expense
            st.markdown("### Remove an Expense")
            if not expenses_df.empty:
                expense_options = [f"{row['Date']} | {row['Description']}" for _, row in expenses_df.iterrows()]
                remove_idx = st.selectbox("Select expense to remove", options=range(len(expenses_df)), format_func=lambda i: expense_options[i], key="remove_select")
                if st.button("Remove Expense", key="remove_expense_btn"):
                    ok, msg = remove_expense(remove_idx, admin_password)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.info("No expenses to remove.")
            st.write("")
            # Reset all records
            st.markdown("### Reset All Records")
            if st.button("Reset All Records", key="reset_all_btn"):
                ok, msg = reset_all_expenses(admin_password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
>>>>>>> 26267d637da151292a3670b81a43afefdcc10abd
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Current Balances")
        balances = calculate_balances()
        
        for friend, balance in balances.items():
            if balance > 0:
                st.success(f"**{friend}**: +PKR {balance:.2f} (to receive)")
            elif balance < 0:
                st.error(f"**{friend}**: PKR {abs(balance):.2f} (to pay)")
            else:
                st.info(f"**{friend}**: PKR 0.00 (settled)")
    
    with col2:
        st.header("Settlements Needed")
        settlements = calculate_settlements(balances)
        
        if settlements:
            for settlement in settlements:
                st.write(f"• {settlement}")
        else:
            st.success("All settled! 🎉")
    
    # Expense history
    st.header("Expense History")
    expenses_df = load_expenses()
    
    if not expenses_df.empty:
        # Display expenses in reverse chronological order
        expenses_df_display = expenses_df.copy()
        expenses_df_display['amount'] = expenses_df_display['amount'].apply(lambda x: f"PKR {float(x):.2f}")
        st.dataframe(expenses_df_display.iloc[::-1], use_container_width=True)
        
        # Download CSV button
        csv_data = expenses_df.to_csv(index=False)
        st.download_button(
            label="Download Expenses CSV",
            data=csv_data,
            file_name="friends_expenses.csv",
            mime="text/csv"
        )
        
        # Show Sheety/Google Sheets link
        sheet_url = st.secrets["sheety"].get("sheet_url", "")
        if sheet_url:
            st.markdown(f"📊 [View Live Google Sheet]({sheet_url})")
    else:
        st.info("No expenses recorded yet. Add your first expense using the sidebar!")

if __name__ == "__main__":
    main()
    expenses_df = load_expenses()
    
    if not expenses_df.empty:
        # Display expenses in reverse chronological order
        expenses_df_display = expenses_df.copy()
        expenses_df_display['Amount'] = expenses_df_display['Amount'].apply(lambda x: f"PKR {float(x):.2f}")
        st.dataframe(expenses_df_display.iloc[::-1], use_container_width=True)
        
        # Download CSV button
        csv_data = expenses_df.to_csv(index=False)
        st.download_button(
            label="Download Expenses CSV",
            data=csv_data,
            file_name="friends_expenses.csv",
            mime="text/csv"
        )
        
        # Show Google Sheets link
        sheet = init_google_sheets()
        if sheet:
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet.spreadsheet.id}"
            st.markdown(f"📊 [View Live Google Sheet]({sheet_url})")
    else:
        st.info("No expenses recorded yet. Add your first expense using the sidebar!")

if __name__ == "__main__":
    main()
