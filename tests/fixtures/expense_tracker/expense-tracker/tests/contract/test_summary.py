# Generated from the Contract. Do not edit.
from app.schemas.custom import MonthlySummaryResponse

from tests.contract.helpers import check_shape


def test_monthly_summary(client):
    res = client.get("/api/summary", params={"month": "2026-11"})
    assert res.status_code == 200
    check_shape(res.json(), MonthlySummaryResponse)
