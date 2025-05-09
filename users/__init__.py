# users/__init__.py
from flask import Blueprint
users_bp = Blueprint('users', __name__)

from .auth import signup,forgot,login
from .enroll import enroll, shop, view,dashboard
from .practice import questions
from .purchase import addcart,coupon,payment, purchase,success