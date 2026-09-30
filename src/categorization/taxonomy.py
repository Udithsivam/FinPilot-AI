"""FinPilot's canonical expense-category taxonomy.

Single source of truth: both the synthetic transaction-data generator
(scripts/generate_transaction_data.py) and the categorization model's
label space (src/categorization/train.py) import this file, so the
generator's labels and the classifier's output space are always the
same taxonomy by construction — not two independently-maintained lists
that could drift apart.

Only covers expense categories. Income transactions use their own
source label (Salary, Freelance Income, ...) — categorizing income
isn't the same problem (there's no ambiguous merchant text to resolve),
so it's out of scope for this classifier.
"""

TAXONOMY: dict[str, dict[str, list[str]]] = {
    "Housing": {
        "Rent": ["Monthly Rent Payment", "Landlord Transfer", "House Rent"],
        "Maintenance": ["Plumber Service", "Electrician Visit", "Home Repair Work"],
    },
    "Food": {
        "Restaurants": ["Dine-in Restaurant Bill", "Pizza Hut", "Domino's Pizza"],
        "Food Delivery": ["Swiggy Order", "Zomato Order", "Uber Eats Order"],
        "Cafes": ["Starbucks", "Cafe Coffee Day", "Local Cafe"],
    },
    "Groceries": {
        "Supermarket": ["BigBasket Order", "DMart Purchase", "Reliance Fresh"],
        "Household Supplies": ["Local Kirana Store", "Household Essentials"],
    },
    "Transportation": {
        "Fuel": ["Indian Oil Petrol Pump", "HP Petrol Pump", "Shell Fuel Station"],
        "Public Transport": ["Metro Card Recharge", "Bus Pass Renewal"],
        "Taxi/Ride Share": ["Uber Ride", "Ola Cabs"],
        "Parking": ["Mall Parking Fee", "Airport Parking"],
    },
    "Utilities": {
        "Electricity": ["State Electricity Board Bill"],
        "Water": ["Municipal Water Supply Bill"],
        "Internet": ["Airtel Broadband Bill", "Jio Fiber Bill"],
        "Mobile": ["Airtel Prepaid Recharge", "Jio Recharge"],
    },
    "Healthcare": {
        "Medicine": ["Apollo Pharmacy", "MedPlus Pharmacy"],
        "Hospital": ["City Hospital Bill"],
        "Doctor": ["Doctor Consultation Fee"],
        "Diagnostics": ["Diagnostic Lab Test"],
    },
    "Education": {
        "Tuition": ["School Tuition Fee", "College Semester Fee"],
        "Books": ["Bookstore Purchase"],
        "Courses": ["Udemy Course", "Coursera Subscription"],
        "Supplies": ["Stationery Store Purchase"],
    },
    "Entertainment": {
        "Movies": ["PVR Cinemas", "INOX Movie Ticket"],
        "Events": ["Concert Ticket", "Event Booking"],
        "Games": ["Steam Game Purchase", "PlayStation Store"],
    },
    "Shopping": {
        "Electronics": ["Amazon Electronics", "Croma Store"],
        "Clothing": ["Myntra Order", "Zara Purchase"],
        "General Shopping": ["Amazon Order", "Flipkart Order"],
    },
    "Insurance": {
        "Health Insurance": ["Health Insurance Premium"],
        "Vehicle Insurance": ["Vehicle Insurance Premium"],
        "Life Insurance": ["LIC Premium Payment"],
    },
    "Loan/Debt": {
        "EMI": ["Home Loan EMI", "Car Loan EMI"],
        "Credit Card Payment": ["Credit Card Bill Payment"],
    },
    "Investments": {
        "Mutual Fund": ["SIP Mutual Fund Investment"],
        "Stocks": ["Zerodha Stock Purchase"],
        "Savings/Deposit": ["Fixed Deposit"],
    },
    "Travel": {
        "Flights": ["IndiGo Flight Booking", "Air India Booking"],
        "Hotels": ["OYO Hotel Booking", "Taj Hotel Booking"],
        "Travel": ["MakeMyTrip Booking"],
    },
    "Personal Care": {
        "Salon": ["Salon Service"],
        "Fitness": ["Gym Membership Fee", "Cult Fit Membership"],
    },
    "Subscriptions": {
        "Streaming": ["Netflix Subscription", "Amazon Prime Subscription"],
        "Software": ["Adobe Subscription", "Microsoft 365 Subscription"],
        "Memberships": ["Club Membership Fee"],
    },
    "Other": {
        "Miscellaneous": ["Miscellaneous Expense"],
    },
}

INCOME_SOURCES = ["Salary", "Freelance Income", "Business Income", "Investment Returns", "Other Income"]


def top_level_categories() -> list[str]:
    return list(TAXONOMY.keys())


def subcategories(category: str) -> list[str]:
    return list(TAXONOMY.get(category, {}).keys())


def joint_labels() -> list[str]:
    """Every "Category > Subcategory" label the classifier can predict."""
    return [f"{cat} > {sub}" for cat, subs in TAXONOMY.items() for sub in subs]


def split_joint_label(label: str) -> tuple[str, str]:
    category, _, subcategory = label.partition(" > ")
    return category, subcategory
