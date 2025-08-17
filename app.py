import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Firebase configuration for pyrebase (for authentication)
firebaseConfig = {
    "apiKey": "AIzaSyDNp0GcpJC-TGx0ewdAk85KdU1db0L0nKM",
    "authDomain": "fir-authenticationstreamli.firebaseapp.com",
    "projectId": "fir-authenticationstreamli",
    "storageBucket": "fir-authenticationstreamli.firebasestorage.app",
    "messagingSenderId": "369955598660",
    "appId": "1:369955598660:web:1dc9ec3cd766be7de8a711",
    "databaseURL": ""
}

# Initialize pyrebase for authentication
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Initialize Firestore
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")  # Path to your downloaded service account key
    firebase_admin.initialize_app(cred)
db = firestore.client()

def signup(email, password):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        return user
    except Exception as e:
        st.error(f"Sign up failed: {e}")
        return None

def login(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        st.error(f"Login failed: {e}")
        return None

def create_group(group_name, members):
    group_data = {
        "name": group_name,
        "members": members,
        "created_at": datetime.now().isoformat()
    }
    try:
        db.collection("groups").add(group_data)
        return True
    except Exception as e:
        st.error("Failed to create group. Check your Firestore permissions.")
        return False

def get_groups_for_user(email):
    try:
        groups_ref = db.collection("groups")
        query = groups_ref.where("members", "array_contains", email).stream()
        user_groups = []
        for doc in query:
            user_groups.append({"key": doc.id, "data": doc.to_dict()})
        return user_groups
    except Exception as e:
        return []

def add_expense(group_key, amount, payer, participants, contributions, remark):
    expense_data = {
        "amount": amount,
        "payer": payer,
        "participants": participants,
        "contributions": contributions,
        "remark": remark,
        "timestamp": datetime.now().isoformat()
    }
    db.collection("groups").document(group_key).collection("expenses").add(expense_data)

def get_expenses(group_key):
    expenses_ref = db.collection("groups").document(group_key).collection("expenses")
    docs = expenses_ref.stream()
    return [doc.to_dict() for doc in docs]

def calculate_balances(group_data, group_key):
    balances = {member: 0 for member in group_data["members"]}
    expenses = get_expenses(group_key)
    for exp in expenses:
        amount = float(exp["amount"])
        payer = exp["payer"]
        participants = exp["participants"]
        contributions = exp["contributions"]
        split = amount / len(participants)
        for p in participants:
            paid = float(contributions.get(p, 0))
            balances[p] -= split
            balances[p] += paid
    return balances

def add_member_to_group(group_key, member_email):
    group_ref = db.collection("groups").document(group_key)
    group = group_ref.get().to_dict()
    if member_email not in group["members"]:
        group["members"].append(member_email)
        group_ref.update({"members": group["members"]})

def remove_member_from_group(group_key, member_email):
    group_ref = db.collection("groups").document(group_key)
    group = group_ref.get().to_dict()
    if member_email in group["members"]:
        group["members"].remove(member_email)
        group_ref.update({"members": group["members"]})

def expense_manager(email):
    st.title("Friends Expense Manager")
    st.sidebar.header("Controls")
    user_groups = get_groups_for_user(email)
    group_names = [g["data"]["name"] for g in user_groups]
    group_keys = [g["key"] for g in user_groups]
    selected_group = st.sidebar.selectbox("Select Group", group_names)
    group_idx = group_names.index(selected_group) if selected_group else None
    group_key = group_keys[group_idx] if group_idx is not None else None
    group_data = user_groups[group_idx]["data"] if group_idx is not None else None

    st.sidebar.subheader("Create New Group")
    new_group_name = st.sidebar.text_input("Group Name")
    new_members = st.sidebar.text_area("Members (comma separated emails)")
    if st.sidebar.button("Create Group"):
        members = [m.strip() for m in new_members.split(",") if m.strip()]
        if email not in members:
            members.append(email)
        success = create_group(new_group_name, members)
        if success:
            st.sidebar.success("Group created!")

    if group_data:
        st.sidebar.subheader("Manage Members")
        st.sidebar.write("Current Members:")
        st.sidebar.write(", ".join(group_data["members"]))
        add_member_email = st.sidebar.text_input("Add Member (email)", key="add_member")
        if st.sidebar.button("Add Member"):
            if add_member_email and add_member_email not in group_data["members"]:
                add_member_to_group(group_key, add_member_email)
                st.sidebar.success(f"Added member: {add_member_email}")
        remove_member_email = st.sidebar.selectbox("Remove Member", [m for m in group_data["members"] if m != email], key="remove_member")
        if st.sidebar.button("Remove Member"):
            if remove_member_email:
                remove_member_from_group(group_key, remove_member_email)
                st.sidebar.success(f"Removed member: {remove_member_email}")

        st.subheader("Add Expense")
        amount = st.number_input("Amount", min_value=0.0)
        payer = st.selectbox("Who paid?", group_data["members"])
        participants = st.multiselect("Who was present?", group_data["members"], default=group_data["members"])
        contributions = {}
        for p in participants:
            contributions[p] = st.number_input(f"Contribution by {p}", min_value=0.0, key=f"contrib_{p}")
        remark = st.text_input("Remark")
        if st.button("Add Expense"):
            add_expense(group_key, amount, payer, participants, contributions, remark)
            st.success("Expense added!")

        st.subheader("Expenses")
        expenses = get_expenses(group_key)
        for exp in expenses:
            st.write(f"{exp['timestamp']}: {exp['remark']} - {exp['amount']} paid by {exp['payer']} for {', '.join(exp['participants'])}")

        st.subheader("Balances")
        balances = calculate_balances(group_data, group_key)
        for member, bal in balances.items():
            st.write(f"{member}: {'Receives' if bal > 0 else 'Owes'} {abs(bal):.2f}")

def main():
    # st.title("Friends Expense Manager")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "email" not in st.session_state:
        st.session_state.email = ""

    if not st.session_state.logged_in:
        st.sidebar.header("Authentication")
        choice = st.sidebar.radio("Login or Sign Up", ["Login", "Sign Up"])
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")

        if choice == "Sign Up":
            if st.sidebar.button("Sign Up"):
                user = signup(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.email = email
        else:
            if st.sidebar.button("Login"):
                user = login(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.email = email
    else:
        expense_manager(st.session_state.email)

if __name__ == "__main__":
    main()