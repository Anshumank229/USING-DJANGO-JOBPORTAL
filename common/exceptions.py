"""
A custom DRF exception handler so every API error comes back in one
consistent shape, instead of DRF's default (which varies by exception type):

    {
      "error": {
        "message": "Human-readable summary",
        "details": { ... original DRF error data ... }
      }
    }

This makes the API predictable for any frontend/mobile client to consume,
and is a common thing interviewers ask about ("how do you handle errors
consistently across an API").
"""

from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        # An unhandled exception (e.g. a bug) — let Django's normal 500
        # handling take over in DEBUG, but keep the shape consistent
        # for anything DRF *did* catch.
        return response

    if isinstance(response.data, dict) and 'detail' in response.data:
        message = response.data['detail']
    elif isinstance(response.data, dict):
        # Serializer validation errors: {"field": ["error", ...], ...}
        message = 'Validation failed.'
    else:
        message = 'An error occurred.'

    response.data = {
        'error': {
            'message': str(message),
            'details': response.data,
        }
    }
    return response
