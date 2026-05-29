import sys
import types


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)

from src.pipeline.job_filter import us_location


def test_us_location_recognizes_common_us_city_region_and_remote_forms():
    for location in (
        "San Francisco / Bay Area",
        "Bay Area",
        "NYC Head Office",
        "New York",
        "New York, NY",
        "Remote U.S.",
        "Remote US",
        "remote within US timezones",
        "Oakland, CA (or remote within US timezones)",
    ):
        assert us_location(location, "ashby") is True


def test_us_location_rejects_foreign_locations():
    for location in (
        "London",
        "Europe",
        "India",
        "Singapore",
        "Cyprus",
    ):
        assert us_location(location, "ashby") is False
