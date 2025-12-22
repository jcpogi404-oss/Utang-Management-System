# Store Credit Management System

A web-based credit management system for tracking customer credits and payments.

## Features
- Add new credit entries with customer name, product, cost, and payment date
- View all credit records in a beautiful interface
- Mark credits as paid
- Delete credit records
- Search credits by customer name
- View summary statistics (total pending, paid, and all credits)

## Requirements
- Python 3.7+
- MySQL Server
- Flask
- mysql-connector-python

## Setup Instructions

### 1. Install MySQL
Make sure MySQL is installed and running on your system.

### 2. Create Database
Run the SQL script to create the database and table:
```bash
mysql -u root -p < database_schema.sql
```

Or manually create it by logging into MySQL:
```bash
mysql -u root -p
```
Then paste the contents of `database_schema.sql`.

### 3. Configure Database Connection
Edit `app.py` and update the database configuration:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Your MySQL username
    'password': '',  # Your MySQL password
    'database': 'store_credit_system'
}
```

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```

The application will be available at: http://localhost:5000

## Usage

### Adding a Credit
1. Fill in the form with:
   - Customer Name
   - Product
   - Cost
   - Estimated Payment Date
2. Click "Add Credit"

### Marking as Paid
- Click the "Mark Paid" button next to a pending credit

### Deleting a Credit
- Click the "Delete" button next to a credit record
- Confirm the deletion

### Searching
- Use the search box to find credits by customer name

## Database Schema

**Table: credits**
- `id` - Auto-incrementing primary key
- `customer_name` - Customer's name
- `product` - Product purchased
- `cost` - Cost of the product
- `estimated_payment_date` - When customer expects to pay
- `created_at` - When the credit was created
- `status` - pending or paid
- `paid_date` - When the credit was marked as paid

## Technologies Used
- Backend: Flask (Python)
- Database: MySQL
- Frontend: HTML, CSS (with responsive design)
- No external CSS frameworks - pure CSS styling

## Notes
- The currency symbol is set to ₱ (Philippine Peso). You can change it in `index.html` if needed.
- The application runs in debug mode by default. For production, set `debug=False` in `app.py`.
