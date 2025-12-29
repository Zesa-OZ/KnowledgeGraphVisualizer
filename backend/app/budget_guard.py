from __future__ import annotations

import time
import calendar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import HTTPException


@dataclass
class BudgetStatus:
    month_key: str
    spent_usd: float
    budget_usd: float
    hard_cap_active: bool  # True si hemos podido consultar Costs API


class BudgetGuard:

    def __init__(self, *, admin_key: str, project_id: str, budget_usd: float, cache_seconds: int):
        self.admin_key = (admin_key or "").strip()
        self.project_id = (project_id or "").strip()
        self.budget_usd = float(budget_usd)
        self.cache_seconds = int(cache_seconds)

        self._cached_month_key: Optional[str] = None
        self._cached_spent_usd: Optional[float] = None
        self._cached_at: float = 0.0
        self._hard_cap_active: bool = False

    def _month_key_utc(self) -> str:
        now = datetime.now(timezone.utc)
        return f"{now.year:04d}-{now.month:02d}"

    def _month_start_unix_utc(self) -> int:
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        return calendar.timegm(start.timetuple())

    def _fetch_costs_month_to_date(self) -> float:
        # Costs endpoint docs:
        # GET https://api.openai.com/v1/organization/costs?start_time=...
        # Example uses OPENAI_ADMIN_KEY. :contentReference[oaicite:1]{index=1}
        start_time = self._month_start_unix_utc()

        params = {
            "start_time": start_time,
            "bucket_width": "1d",
            "limit": 180,
        }

        # Si sabemos el project_id, filtramos por project_ids
        if self.project_id:
            # OpenAI acepta arrays en query; httpx lo maneja con lista de tuplas:
            # project_ids=proj_xxx&project_ids=proj_yyy
            pass

        headers = {
            "Authorization": f"Bearer {self.admin_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=30) as client:
            if self.project_id:
                # repetimos project_ids como query params
                query = list(params.items()) + [("project_ids", self.project_id)]
                r = client.get("https://api.openai.com/v1/organization/costs", params=query, headers=headers)
            else:
                r = client.get("https://api.openai.com/v1/organization/costs", params=params, headers=headers)

            r.raise_for_status()
            data = r.json()

        # Suma de amount.value de todos los buckets/results
        total = 0.0
        for bucket in data.get("data", []):
            for item in bucket.get("results", []):
                amount = (item.get("amount") or {})
                val = amount.get("value")
                if isinstance(val, (int, float)):
                    total += float(val)

        return total

    def get_status(self) -> BudgetStatus:
        month_key = self._month_key_utc()

        # cache por tiempo y por mes
        if (
            self._cached_month_key == month_key
            and self._cached_spent_usd is not None
            and (time.time() - self._cached_at) < self.cache_seconds
        ):
            return BudgetStatus(
                month_key=month_key,
                spent_usd=self._cached_spent_usd,
                budget_usd=self.budget_usd,
                hard_cap_active=self._hard_cap_active,
            )

        # Si no hay admin_key, no podemos consultar Costs API
        if not self.admin_key:
            self._cached_month_key = month_key
            self._cached_spent_usd = 0.0
            self._cached_at = time.time()
            self._hard_cap_active = False
            return BudgetStatus(
                month_key=month_key,
                spent_usd=0.0,
                budget_usd=self.budget_usd,
                hard_cap_active=False,
            )

        # Si hay admin_key, intentamos Costs API
        try:
            spent = self._fetch_costs_month_to_date()
            self._hard_cap_active = True
        except Exception:
            # Si falla, no bloqueamos (para no romper prod/dev por un endpoint temporalmente caído)
            spent = 0.0
            self._hard_cap_active = False

        self._cached_month_key = month_key
        self._cached_spent_usd = float(spent)
        self._cached_at = time.time()

        return BudgetStatus(
            month_key=month_key,
            spent_usd=float(spent),
            budget_usd=self.budget_usd,
            hard_cap_active=self._hard_cap_active,
        )

    def enforce_or_raise(self) -> BudgetStatus:
        status = self.get_status()

        # Solo hacemos hard-block si:
        # - budget_enforce está activo (lo decide el caller)
        # - y el hard cap está activo (Costs API OK)
        if status.hard_cap_active and status.spent_usd >= status.budget_usd:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly budget exceeded ({status.spent_usd:.2f}$ / {status.budget_usd:.2f}$).",
            )

        return status
