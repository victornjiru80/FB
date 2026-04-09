# templatetags/math_extras.py
from django import template
import re

register = template.Library()

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def get_item(obj, key):
    """Get an item from a dictionary or object attribute by key"""
    if isinstance(obj, dict):
        return obj.get(key)
    elif hasattr(obj, key):
        return getattr(obj, key)
    return None

@register.filter
def parse_acknowledgement_notes(notes_text):
    """Parse acknowledgement notes from additional_notes field"""
    if not notes_text:
        return []

    # Find all acknowledgement note sections
    pattern = r'--- Acknowledgment Note \([^)]+\) ---\s*(.*?)(?=\n\n---|$)'
    matches = re.findall(pattern, notes_text, re.DOTALL)

    # Clean up the notes (remove extra whitespace)
    return [note.strip() for note in matches if note.strip()]