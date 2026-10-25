"""Graduation & Pictorial Toga ("Pajah") Rental API Bridge."""

from __future__ import annotations

from typing import Any, Dict, List

from app.api.base import BaseAPI
from app.core.decimal_utils import to_decimal
from app.core.pajah_engine import (
    DEFAULT_OWNERS,
    PajahOwnerRecord,
    calculate_pajah_summary,
)


class PajahAPI(BaseAPI):
    """API endpoints for graduation toga rental revenue and owner distribution."""

    def compute_pajah_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute pictorial and graduation toga rentals, pricing, and revenues."""
        try:
            owners_raw = payload.get("owners")
            if owners_raw is not None:
                records = [
                    PajahOwnerRecord(
                        owner_name=o.get("owner_name", "Owner"),
                        owned=int(o.get("owned", 1)),
                        price_pictorial=to_decimal(o.get("price_pictorial", "500.00")),
                        price_grad=to_decimal(o.get("price_grad", "650.00")),
                        dan_addon=to_decimal(o.get("dan_addon", "100.00")),
                        active_rentals=int(o.get("active_rentals", 0)),
                    )
                    for o in owners_raw
                ]
                res = calculate_pajah_summary(records)
            else:
                res = calculate_pajah_summary()

            return self.success(res)
        except Exception as e:
            return self.error(f"Failed to calculate pajah summary: {str(e)}")
