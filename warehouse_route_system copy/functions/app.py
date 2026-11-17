import sys
import os
import io
import urllib.parse
import base64

# Add project root directory to sys.path so app modules can be loaded
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

# Try importing serverless_wsgi; if not available, use built-in WSGI adapter
try:
    import serverless_wsgi
    HAS_SERVERLESS_WSGI = True
except ImportError:
    HAS_SERVERLESS_WSGI = False


def lambda_wsgi_adapter(wsgi_app, event, context):
    """Zero-dependency AWS Lambda / Netlify WSGI adapter for Flask."""
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    qs = event.get('queryStringParameters') or {}
    query_string = urllib.parse.urlencode(qs)
    
    headers = event.get('headers') or {}
    body = event.get('body', '') or ''
    if event.get('isBase64Encoded', False):
        body_bytes = base64.b64decode(body)
    else:
        body_bytes = body.encode('utf-8')

    environ = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'SERVER_NAME': headers.get('host', 'localhost'),
        'SERVER_PORT': '443' if headers.get('x-forwarded-proto') == 'https' else '80',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': headers.get('x-forwarded-proto', 'https'),
        'wsgi.input': io.BytesIO(body_bytes),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'CONTENT_LENGTH': str(len(body_bytes)),
        'CONTENT_TYPE': headers.get('content-type', '')
    }

    for key, value in headers.items():
        key_upper = key.upper().replace('-', '_')
        if key_upper not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key_upper}'] = value

    response_status = [200]
    response_headers = []

    def start_response(status, headers_list, exc_info=None):
        response_status[0] = int(status.split(' ')[0])
        response_headers.extend(headers_list)

    result = wsgi_app(environ, start_response)
    response_body = b''.join(result)

    headers_dict = {}
    multi_headers = {}
    for k, v in response_headers:
        if k.lower() == 'set-cookie':
            multi_headers.setdefault(k, []).append(v)
        else:
            headers_dict[k] = v

    is_text = any(
        headers_dict.get(h, '').startswith(('text/', 'application/json', 'application/javascript'))
        for h in headers_dict
    )

    if is_text or not response_body:
        try:
            body_str = response_body.decode('utf-8')
            is_b64 = False
        except UnicodeDecodeError:
            body_str = base64.b64encode(response_body).decode('ascii')
            is_b64 = True
    else:
        body_str = base64.b64encode(response_body).decode('ascii')
        is_b64 = True

    response = {
        'statusCode': response_status[0],
        'headers': headers_dict,
        'body': body_str,
        'isBase64Encoded': is_b64
    }
    if multi_headers:
        response['multiValueHeaders'] = multi_headers

    return response


def handler(event, context):
    """Main Netlify Functions Entrypoint."""
    if HAS_SERVERLESS_WSGI:
        return serverless_wsgi.handle_request(app, event, context)
    return lambda_wsgi_adapter(app, event, context)
