from flask import Blueprint
admin_bp = Blueprint('admin', __name__)

from .auth import login
from .question import question
from .manage import book, courses