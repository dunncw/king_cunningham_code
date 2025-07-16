import os
import base64
import json
from datetime import datetime

def format_date(date_obj):
    """Format a date object for Simplifile API"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%m/%d/%Y")
    return date_obj