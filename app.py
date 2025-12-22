from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL username
    'password': '',  # Change this to your MySQL password
    'database': 'store_credit_system'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
def index():
    """Main page - display all credits"""
    connection = get_db_connection()
    if not connection:
        return "Database connection error", 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, customer_name, product, cost, 
                   estimated_payment_date, status, created_at, paid_date
            FROM credits 
            ORDER BY created_at DESC
        """)
        credits = cursor.fetchall()
        
        # Calculate totals
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'pending' THEN cost ELSE 0 END) as total_pending,
                SUM(CASE WHEN status = 'paid' THEN cost ELSE 0 END) as total_paid,
                SUM(cost) as total_all
            FROM credits
        """)
        totals = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return render_template('index.html', credits=credits, totals=totals)
    except Error as e:
        print(f"Database error: {e}")
        return f"Database error: {e}", 500

@app.route('/add_credit', methods=['POST'])
def add_credit():
    """Add a new credit entry"""
    customer_name = request.form.get('customer_name')
    product = request.form.get('product')
    cost = request.form.get('cost')
    estimated_payment_date = request.form.get('estimated_payment_date')
    
    if not all([customer_name, product, cost, estimated_payment_date]):
        return jsonify({'error': 'All fields are required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO credits (customer_name, product, cost, estimated_payment_date)
            VALUES (%s, %s, %s, %s)
        """, (customer_name, product, float(cost), estimated_payment_date))
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect(url_for('index'))
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/mark_paid/<int:credit_id>', methods=['POST'])
def mark_paid(credit_id):
    """Mark a credit as paid"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE credits 
            SET status = 'paid', paid_date = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (credit_id,))
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect(url_for('index'))
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_credit/<int:credit_id>', methods=['POST'])
def delete_credit(credit_id):
    """Delete a credit entry"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM credits WHERE id = %s", (credit_id,))
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect(url_for('index'))
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search')
def search():
    """Search credits by customer name"""
    query = request.args.get('q', '')
    connection = get_db_connection()
    if not connection:
        return "Database connection error", 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, customer_name, product, cost, 
                   estimated_payment_date, status, created_at, paid_date
            FROM credits 
            WHERE customer_name LIKE %s
            ORDER BY created_at DESC
        """, (f'%{query}%',))
        credits = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'pending' THEN cost ELSE 0 END) as total_pending,
                SUM(CASE WHEN status = 'paid' THEN cost ELSE 0 END) as total_paid,
                SUM(cost) as total_all
            FROM credits
            WHERE customer_name LIKE %s
        """, (f'%{query}%',))
        totals = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return render_template('index.html', credits=credits, totals=totals, search_query=query)
    except Error as e:
        print(f"Database error: {e}")
        return f"Database error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
