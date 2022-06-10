import os

bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', 5000)}"
