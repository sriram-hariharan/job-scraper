from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from src.utils.logging import get_logger

logger = get_logger("parallel")

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
                logger.warning(f"worker failed: {e}")

    return results