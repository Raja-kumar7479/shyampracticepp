from flask import render_template, request, redirect, url_for, flash
from extensions import admin_login_required
from admin.manage.book_db import UserOperation
from admin import admin_bp

user_op = UserOperation()

@admin_bp.route('/manage_books')
@admin_login_required
def manage_books():
    code = request.args.get('code', '').upper()
    books = user_op.get_books_for_course(code) if code else []
    return render_template('admin/manage/book.html', code=code, books=books)

@admin_bp.route('/add_book', methods=['POST'])
@admin_login_required
def add_book():
    code = request.form['code'].strip().upper()
    title = request.form['title'].strip()
    url = request.form['url'].strip()

    existing = user_op.get_books_for_course(code)
    if any(b['title'] == title and b['url'] == url for b in existing):
        flash("Book already exists!", "warning")
    else:
        user_op.insert_book(code, title, url)
        flash("Book added successfully!", "success")
    return redirect(url_for('admin.manage_books', code=code))

@admin_bp.route('/update_book', methods=['POST'])
@admin_login_required
def update_book():
    code = request.form['code'].strip().upper()
    old_title = request.form['old_title']
    old_url = request.form['old_url']
    new_title = request.form['title'].strip()
    new_url = request.form['url'].strip()

    if new_title == old_title and new_url == old_url:
        flash("No changes detected!", "info")
    else:
        updated = user_op.update_book(code, old_title, new_title, new_url)
        flash("Book updated successfully!" if updated else "Book not found!", "info")
    return redirect(url_for('admin.manage_books', code=code))

@admin_bp.route('/delete_book', methods=['POST'])
@admin_login_required
def delete_book():
    code = request.form['code'].strip().upper()
    title = request.form['title'].strip()
    deleted = user_op.delete_book(code, title)
    flash("Book deleted successfully!" if deleted else "Book not found!", "info")
    return redirect(url_for('admin.manage_books', code=code))
