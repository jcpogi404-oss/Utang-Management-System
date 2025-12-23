from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, session
import sqlite3
from datetime import datetime
import os
from functools import wraps


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'utang-secret-key-change-in-production-2025')

# Login credentials
LOGIN_EMAIL = 'jcpogi@1234'
LOGIN_PASSWORD = '12345'

# Database file path - use /opt/render/project/src for Render deployment
DB_PATH = os.getenv('DB_PATH', '.')
DB_FILE = os.path.join(DB_PATH, 'store_credit.db')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    """Initialize the database with the required table"""
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone_number TEXT,
            estimated_payment_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            paid_date TIMESTAMP NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            cost REAL NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price REAL DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            paid_date TIMESTAMP NULL,
            FOREIGN KEY (credit_id) REFERENCES credits(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_name ON credits(customer_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON credits(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payment_date ON credits(estimated_payment_date)")
    
    # Add status and paid_date columns to credit_items if they don't exist (migration)
    try:
        cursor.execute("ALTER TABLE credit_items ADD COLUMN status TEXT DEFAULT 'pending'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE credit_items ADD COLUMN paid_date TIMESTAMP NULL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add phone_number column to credits if it doesn't exist (migration)
    try:
        cursor.execute("ALTER TABLE credits ADD COLUMN phone_number TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE credit_items ADD COLUMN paid_date TIMESTAMP NULL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    connection.commit()
    connection.close()
    print("Database initialized successfully!")

def get_db_connection():
    """Create and return a database connection"""
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == LOGIN_EMAIL and password == LOGIN_PASSWORD:
            session['logged_in'] = True
            session['user'] = email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid email or password')
    
    # If already logged in, redirect to index
    if 'logged_in' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main page - display all credits"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT c.id, c.customer_name, c.estimated_payment_date, 
                   c.status, c.created_at, c.paid_date,
                   COALESCE(SUM(ci.cost), 0) as total_cost,
                   COUNT(ci.id) as item_count
            FROM credits c
            LEFT JOIN credit_items ci ON c.id = ci.credit_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """)
        credits = cursor.fetchall()
        
        # Get all items for all credits
        cursor.execute("""
            SELECT credit_id, id, product, cost, added_at, quantity, unit_price
            FROM credit_items
            ORDER BY added_at DESC
        """)
        all_items = cursor.fetchall()
        
        # Group items by credit_id
        items_by_credit = {}
        for item in all_items:
            credit_id = item['credit_id']
            if credit_id not in items_by_credit:
                items_by_credit[credit_id] = []
            items_by_credit[credit_id].append(item)
        
        # Calculate totals (all items are pending since paid ones are deleted)
        cursor.execute("""
            SELECT 
                SUM(ci.cost) as total_pending
            FROM credit_items ci
        """)
        totals = cursor.fetchone()
        
        connection.close()
        
        return render_template('index.html', credits=credits, totals=totals, items_by_credit=items_by_credit)
    except Exception as e:
        print(f"Database error: {e}")
        return f"Database error: {e}", 500

@app.route('/add_credit', methods=['POST'])
@login_required
def add_credit():
    """Add a new credit entry"""
    customer_name = request.form.get('customer_name')
    product = request.form.get('product')
    cost = request.form.get('cost')
    estimated_payment_date = request.form.get('estimated_payment_date')
    quantity = request.form.get('quantity', 1)
    price = request.form.get('price', 0)
    
    if not all([customer_name, product, cost, estimated_payment_date]):
        return jsonify({'error': 'All fields are required'}), 400
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert credit record
        cursor.execute("""
            INSERT INTO credits (customer_name, estimated_payment_date)
            VALUES (?, ?)
        """, (customer_name, estimated_payment_date))
        
        credit_id = cursor.lastrowid
        
        # Insert first item
        cursor.execute("""
            INSERT INTO credit_items (credit_id, product, cost, quantity, unit_price)
            VALUES (?, ?, ?, ?, ?)
        """, (credit_id, product, float(cost), int(quantity), float(price)))
        
        connection.commit()
        connection.close()
        
        return redirect(url_for('index', success='added'))
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/mark_paid/<int:credit_id>', methods=['POST'])
@login_required
def mark_paid(credit_id):
    """Mark a credit as paid"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE credits 
            SET status = 'paid', paid_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (credit_id,))
        
        connection.commit()
        connection.close()
        
        return redirect(url_for('index', success='paid'))
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/add_product/<int:credit_id>', methods=['POST'])
@login_required
def add_product(credit_id):
    """Add a new product to an existing credit"""
    product = request.form.get('product')
    cost = request.form.get('cost')
    quantity = request.form.get('quantity', 1)
    price = request.form.get('price', 0)
    
    if not all([product, cost]):
        return jsonify({'error': 'Product and cost are required'}), 400
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert the new product
        cursor.execute("""
            INSERT INTO credit_items (credit_id, product, cost, quantity, unit_price)
            VALUES (?, ?, ?, ?, ?)
        """, (credit_id, product, float(cost), int(quantity), float(price)))
        
        # Change status back to pending if it was paid
        cursor.execute("""
            UPDATE credits 
            SET status = 'pending', paid_date = NULL
            WHERE id = ?
        """, (credit_id,))
        
        connection.commit()
        connection.close()
        
        return redirect(url_for('index', success='product_added'))
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/view_items/<int:credit_id>')
@login_required
def view_items(credit_id):
    """View all items for a specific credit"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get credit info
        cursor.execute("""
            SELECT c.id, c.customer_name, c.estimated_payment_date, 
                   c.status, c.created_at
            FROM credits c
            WHERE c.id = ?
        """, (credit_id,))
        credit = cursor.fetchone()
        
        if not credit:
            connection.close()
            return "Credit not found", 404
        
        # Get all items (only pending ones remain after payment)
        cursor.execute("""
            SELECT id, product, cost, added_at, quantity, unit_price
            FROM credit_items
            WHERE credit_id = ?
            ORDER BY added_at DESC
        """, (credit_id,))
        items = cursor.fetchall()
        
        # Calculate total (all remaining items are pending)
        cursor.execute("""
            SELECT 
                SUM(cost) as total
            FROM credit_items
            WHERE credit_id = ?
        """, (credit_id,))
        total = cursor.fetchone()
        
        connection.close()
        
        return render_template('view_items.html', credit=credit, items=items, total=total)
    except Exception as e:
        print(f"Database error: {e}")
        return f"Database error: {e}", 500

@app.route('/mark_item_paid/<int:credit_id>/<int:item_id>', methods=['POST'])
@login_required
def mark_item_paid(credit_id, item_id):
    """Mark a specific item as paid and remove it"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Delete the paid item
        cursor.execute("""
            DELETE FROM credit_items 
            WHERE id = ? AND credit_id = ?
        """, (item_id, credit_id))
        
        # Check if any items remain for this credit
        cursor.execute("""
            SELECT COUNT(*) as remaining_count
            FROM credit_items
            WHERE credit_id = ?
        """, (credit_id,))
        result = cursor.fetchone()
        
        # If no items remain, mark the whole credit as paid and delete it
        if result['remaining_count'] == 0:
            cursor.execute("""
                UPDATE credits 
                SET status = 'paid', paid_date = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (credit_id,))
        
        connection.commit()
        connection.close()
        
        return redirect(url_for('index', success='item_paid') + '#credit-list')
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_credit/<int:credit_id>', methods=['POST'])
@login_required
def delete_credit(credit_id):
    """Delete a credit entry and reorder IDs"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Delete the credit and its items
        cursor.execute("DELETE FROM credit_items WHERE credit_id = ?", (credit_id,))
        cursor.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
        
        # Reorder IDs: Get all remaining credits ordered by creation date
        cursor.execute("""
            SELECT id FROM credits ORDER BY created_at ASC
        """)
        remaining_credits = cursor.fetchall()
        
        # Temporarily disable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Create temporary table with new sequential IDs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credits_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone_number TEXT,
                estimated_payment_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                paid_date TIMESTAMP NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_items_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_id INTEGER NOT NULL,
                product TEXT NOT NULL,
                cost REAL NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price REAL DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                paid_date TIMESTAMP NULL,
                FOREIGN KEY (credit_id) REFERENCES credits_temp(id) ON DELETE CASCADE
            )
        """)
        
        # Copy data with new sequential IDs
        new_id = 1
        id_mapping = {}  # Old ID -> New ID
        
        for old_credit in remaining_credits:
            old_id = old_credit['id']
            id_mapping[old_id] = new_id
            
            # Copy credit with new ID
            cursor.execute("""
                INSERT INTO credits_temp (id, customer_name, phone_number, estimated_payment_date, created_at, status, paid_date)
                SELECT ?, customer_name, phone_number, estimated_payment_date, created_at, status, paid_date
                FROM credits WHERE id = ?
            """, (new_id, old_id))
            
            # Copy items with new credit_id
            cursor.execute("""
                INSERT INTO credit_items_temp (credit_id, product, cost, quantity, unit_price, added_at, status, paid_date)
                SELECT ?, product, cost, quantity, unit_price, added_at, status, paid_date
                FROM credit_items WHERE credit_id = ?
            """, (new_id, old_id))
            
            new_id += 1
        
        # Drop old tables and rename temp tables
        cursor.execute("DROP TABLE IF EXISTS credit_items")
        cursor.execute("DROP TABLE IF EXISTS credits")
        cursor.execute("ALTER TABLE credits_temp RENAME TO credits")
        cursor.execute("ALTER TABLE credit_items_temp RENAME TO credit_items")
        
        # Reset autoincrement counter
        cursor.execute(f"UPDATE sqlite_sequence SET seq = {new_id - 1} WHERE name = 'credits'")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name = 'credit_items'")
        
        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        connection.commit()
        connection.close()
        
        return redirect(url_for('index', success='deleted'))
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search')
@login_required
def search():
    """Search credits by customer name"""
    query = request.args.get('q', '')
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT c.id, c.customer_name, c.estimated_payment_date, 
                   c.status, c.created_at, c.paid_date,
                   COALESCE(SUM(ci.cost), 0) as total_cost,
                   COUNT(ci.id) as item_count
            FROM credits c
            LEFT JOIN credit_items ci ON c.id = ci.credit_id
            WHERE c.customer_name LIKE ?
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """, (f'%{query}%',))
        credits = cursor.fetchall()
        
        # Get all items for searched credits
        cursor.execute("""
            SELECT ci.credit_id, ci.id, ci.product, ci.cost, ci.added_at, ci.quantity, ci.unit_price
            FROM credit_items ci
            JOIN credits c ON ci.credit_id = c.id
            WHERE c.customer_name LIKE ?
            ORDER BY ci.added_at DESC
        """, (f'%{query}%',))
        all_items = cursor.fetchall()
        
        # Group items by credit_id
        items_by_credit = {}
        for item in all_items:
            credit_id = item['credit_id']
            if credit_id not in items_by_credit:
                items_by_credit[credit_id] = []
            items_by_credit[credit_id].append(item)
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN c.status = 'pending' THEN COALESCE(ci.cost, 0) ELSE 0 END) as total_pending,
                SUM(CASE WHEN c.status = 'paid' THEN COALESCE(ci.cost, 0) ELSE 0 END) as total_paid,
                SUM(COALESCE(ci.cost, 0)) as total_all
            FROM credits c
            LEFT JOIN credit_items ci ON c.id = ci.credit_id
            WHERE c.customer_name LIKE ?
        """, (f'%{query}%',))
        totals = cursor.fetchone()
        
        connection.close()
        
        return render_template('index.html', credits=credits, totals=totals, search_query=query, items_by_credit=items_by_credit)
    except Exception as e:
        print(f"Database error: {e}")
        return f"Database error: {e}", 500

@app.route('/export_credits')
@login_required
def export_credits():
    """Export credits list to a text file"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get all credits with their items
        cursor.execute("""
            SELECT c.id, c.customer_name, c.estimated_payment_date, 
                   c.status, c.created_at,
                   COALESCE(SUM(ci.cost), 0) as total_cost
            FROM credits c
            LEFT JOIN credit_items ci ON c.id = ci.credit_id
            GROUP BY c.id
            ORDER BY c.customer_name, c.created_at DESC
        """)
        credits = cursor.fetchall()
        
        # Build the output text
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("LISTAHAN NG UTANG - TINDAHAN NI ANNIE")
        output_lines.append("=" * 80)
        output_lines.append(f"Petsa ng Pag-export: {datetime.now().strftime('%B %d, %Y - %I:%M %p')}")
        output_lines.append("=" * 80)
        output_lines.append("")
        
        for credit in credits:
            # Get items for this credit
            cursor.execute("""
                SELECT product, cost, added_at, quantity, unit_price
                FROM credit_items
                WHERE credit_id = ?
                ORDER BY added_at DESC
            """, (credit['id'],))
            items = cursor.fetchall()
            
            # Customer header
            output_lines.append("-" * 80)
            output_lines.append(f"KOSTUMER: {credit['customer_name']}")
            output_lines.append(f"ID ng Utang: {credit['id']}")
            output_lines.append(f"Katayuan: {credit['status'].upper()}")
            output_lines.append(f"Tinantyang Petsa ng Bayad: {credit['estimated_payment_date']}")
            output_lines.append(f"Petsa ng Paglikha: {credit['created_at']}")
            output_lines.append("")
            
            # Items list
            if items:
                output_lines.append("  MGA PRODUKTO:")
                output_lines.append("  " + "-" * 76)
                for idx, item in enumerate(items, 1):
                    output_lines.append(f"  {idx}. {item['product']}")
                    output_lines.append(f"     Halaga: ₱{item['cost']:.2f}")
                    output_lines.append(f"     Petsa ng Pagdagdag: {item['added_at']}")
                    output_lines.append("")
            else:
                output_lines.append("  Walang mga produkto")
                output_lines.append("")
            
            # Total
            output_lines.append(f"  KABUUANG UTANG: ₱{credit['total_cost']:.2f}")
            output_lines.append("-" * 80)
            output_lines.append("")
        
        # Summary
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT c.id) as total_credits,
                SUM(CASE WHEN c.status = 'pending' THEN COALESCE(ci.cost, 0) ELSE 0 END) as total_pending,
                SUM(CASE WHEN c.status = 'paid' THEN COALESCE(ci.cost, 0) ELSE 0 END) as total_paid,
                SUM(COALESCE(ci.cost, 0)) as total_all
            FROM credits c
            LEFT JOIN credit_items ci ON c.id = ci.credit_id
        """)
        summary = cursor.fetchone()
        
        output_lines.append("=" * 80)
        output_lines.append("BUOD")
        output_lines.append("=" * 80)
        output_lines.append(f"Kabuuang Bilang ng Utang: {summary['total_credits']}")
        output_lines.append(f"Kabuuang Hindi Pa Bayad: ₱{summary['total_pending']:.2f}")
        output_lines.append(f"Kabuuang Nabayaran: ₱{summary['total_paid']:.2f}")
        output_lines.append(f"KABUUANG LAHAT: ₱{summary['total_all']:.2f}")
        output_lines.append("=" * 80)
        
        connection.close()
        
        # Create the file content
        file_content = "\n".join(output_lines)
        
        # Generate filename with current date
        filename = f"Listahan_ng_Utang_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Return as downloadable file
        return Response(
            file_content,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
        
    except Exception as e:
        print(f"Export error: {e}")
        return f"Export error: {e}", 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    print("=" * 50)
    print("🚀 Utang Record System")
    print("=" * 50)
    print("📍 Access the application at: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # For production (gunicorn)
    init_db()
