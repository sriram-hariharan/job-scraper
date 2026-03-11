import time
import functools
import requests

def retry_request(retries=2, delay=0.5, retry_status=(500, 502, 503, 504)):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            last_response = None

            for attempt in range(retries):

                try:
                    response = func(*args, **kwargs)

                    if response is None:
                        return None

                    last_response = response

                    if response.status_code not in retry_status:
                        return response

                except Exception:
                    pass

                if attempt < retries - 1:
                    time.sleep(delay)

            return last_response

        return wrapper

    return decorator

@retry_request(retries=2)
def http_get(url, **kwargs):
    return requests.get(url, **kwargs)


@retry_request(retries=2)
def http_post(url, **kwargs):
    return requests.post(url, **kwargs)