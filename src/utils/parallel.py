from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def run_parallel(items, worker_fn, max_workers=10, desc="Processing"):

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        futures = [executor.submit(worker_fn, item) for item in items]

        for future in tqdm(as_completed(futures), total=len(futures), desc=desc):
            try:
                res = future.result()
                if res:
                    results.extend(res)
            except Exception as e:
                print(f"Error occurred while processing item in thread pooling at {desc}: {e}")
                pass

    return results