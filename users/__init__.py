from flask import Blueprint

users_bp = Blueprint('users', __name__)


from .auth import (
    signup,
    forgot,
    login,
    google,
    google_set_password
)


from .enroll import (
    enroll,
    shop,
    view,
    dashboard
)


from .question_practice import question


from .checkout import (
    addcart,
    coupon,
    payment,
    purchase,
    success
)


from .mock_test.handler_db import (
    test_handler_db,
    result_handler_db
)


from .mock_test.instruction_handler import (
    instruction,
    readiness,
    violation
)


from .mock_test.test_handler import (
    start_submit_test,
    system_login,
    test_result,
    test_feedback
    
)

from .mock_test.question_handler import (
    fetch_question
    
)

from .mock_test.content_dashboard.free_dashboard import (
    test_dashboard
    
)

from .mock_test.content_dashboard.paid_dashboard import (
    test_dashboard
    
)
