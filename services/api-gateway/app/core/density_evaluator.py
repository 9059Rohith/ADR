"""SentinelArena — Crowd Density Evaluator.

Deterministic statistical analysis of crowd density trends using
Exponentially Weighted Moving Average (EWMA) and linear projection.
This is the numeric core — the LLM only phrases these results, never invents them.

Grounding boundary: all density numbers, thresholds, and projections come from
this module. The LLM receives these as facts and generates natural-language
explanations and recommendations based on them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class SeverityLevel(str, Enum):
    """Crowd density severity classification.

    Thresholds are deterministic and configurable:
    - NORMAL: 0-74% capacity
    - WARNING: 75-84% capacity
    - CRITICAL: 85-94% capacity
    - EMERGENCY: 95%+ capacity
    """

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class DensityReading:
    """A single crowd density reading for a zone."""

    zone_id: str
    count: int
    capacity: int
    timestamp: datetime

    @property
    def density_pct(self) -> float:
        """Current density as a percentage of capacity."""
        if self.capacity <= 0:
            return 0.0
        return min((self.count / self.capacity) * 100.0, 100.0)


@dataclass
class TrendAnalysis:
    """Result of EWMA trend analysis for a zone."""

    zone_id: str
    zone_name: str
    current_density_pct: float
    ewma_density_pct: float
    trend_direction: str  # "rising", "falling", "stable"
    trend_rate_pct_per_min: float
    severity: SeverityLevel
    projected_time_to_threshold_min: float | None
    projected_peak_pct: float | None
    current_count: int
    capacity: int
    timestamp: datetime

    @property
    def is_actionable(self) -> bool:
        """Whether this trend warrants attention."""
        return (
            self.severity in (SeverityLevel.WARNING, SeverityLevel.CRITICAL, SeverityLevel.EMERGENCY)
            or (self.trend_direction == "rising" and self.current_density_pct > 60.0)
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API response / LLM consumption.

        This is the structured data the LLM receives as ground truth.
        The LLM must not invent any numbers beyond what's in this dict.
        """
        return {
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "current_density_pct": round(self.current_density_pct, 1),
            "ewma_density_pct": round(self.ewma_density_pct, 1),
            "trend_direction": self.trend_direction,
            "trend_rate_pct_per_min": round(self.trend_rate_pct_per_min, 2),
            "severity": self.severity.value,
            "projected_time_to_threshold_min": (
                round(self.projected_time_to_threshold_min, 1)
                if self.projected_time_to_threshold_min is not None
                else None
            ),
            "projected_peak_pct": (
                round(self.projected_peak_pct, 1)
                if self.projected_peak_pct is not None
                else None
            ),
            "current_count": self.current_count,
            "capacity": self.capacity,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CrowdAdvisory:
    """Generated advisory for the control room."""

    zone_id: str
    zone_name: str
    severity: SeverityLevel
    trend_data: TrendAnalysis
    advisory_text: str  # Populated by the LLM
    recommended_actions: list[str]  # Populated by the LLM
    sources: list[str]  # Citation list
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API response."""
        return {
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "severity": self.severity.value,
            "trend_data": self.trend_data.to_dict(),
            "advisory_text": self.advisory_text,
            "recommended_actions": self.recommended_actions,
            "sources": self.sources,
            "created_at": self.created_at.isoformat(),
        }


class DensityEvaluator:
    """Evaluates crowd density trends using EWMA and linear projection.

    All numeric analysis is deterministic. The evaluator:
    1. Maintains a sliding window of readings per zone
    2. Computes EWMA for smoothed trend detection
    3. Classifies severity based on configurable thresholds
    4. Projects time-to-threshold using linear extrapolation

    The LLM layer (Crowd Agent) receives these results as ground truth
    and generates human-readable advisories and recommendations.
    """

    # Severity thresholds (percentage of capacity)
    THRESHOLD_WARNING: float = 75.0
    THRESHOLD_CRITICAL: float = 85.0
    THRESHOLD_EMERGENCY: float = 95.0

    # EWMA decay factor (0-1, higher = more responsive to recent data)
    EWMA_ALPHA: float = 0.3

    # Trend stability threshold (pct/min below this = "stable")
    TREND_STABLE_THRESHOLD: float = 0.5

    # Maximum readings to keep per zone (sliding window)
    MAX_READINGS: int = 120  # 10 minutes at 5s intervals

    def __init__(self) -> None:
        self._readings: dict[str, list[DensityReading]] = {}
        self._ewma: dict[str, float] = {}
        self._zone_names: dict[str, str] = {}

    def register_zone(self, zone_id: str, zone_name: str) -> None:
        """Register a zone for tracking."""
        self._zone_names[zone_id] = zone_name
        if zone_id not in self._readings:
            self._readings[zone_id] = []
            self._ewma[zone_id] = 0.0

    def add_reading(self, reading: DensityReading) -> TrendAnalysis:
        """Add a new density reading and compute the updated trend analysis.

        Args:
            reading: The new density reading.

        Returns:
            Updated trend analysis for the zone.
        """
        zone_id = reading.zone_id

        if zone_id not in self._readings:
            self._readings[zone_id] = []
            self._ewma[zone_id] = reading.density_pct
            self._zone_names.setdefault(zone_id, f"Zone-{zone_id[:8]}")

        readings = self._readings[zone_id]
        readings.append(reading)

        # Trim sliding window
        if len(readings) > self.MAX_READINGS:
            readings[:] = readings[-self.MAX_READINGS :]

        # Update EWMA
        prev_ewma = self._ewma[zone_id]
        new_ewma = self.EWMA_ALPHA * reading.density_pct + (1 - self.EWMA_ALPHA) * prev_ewma
        self._ewma[zone_id] = new_ewma

        # Compute trend
        trend_rate = self._compute_trend_rate(readings)
        trend_direction = self._classify_trend(trend_rate)
        severity = self._classify_severity(reading.density_pct)

        # Project time to next threshold
        projected_time = self._project_time_to_threshold(
            reading.density_pct, trend_rate, severity
        )
        projected_peak = self._project_peak(reading.density_pct, trend_rate)

        return TrendAnalysis(
            zone_id=zone_id,
            zone_name=self._zone_names.get(zone_id, f"Zone-{zone_id[:8]}"),
            current_density_pct=reading.density_pct,
            ewma_density_pct=new_ewma,
            trend_direction=trend_direction,
            trend_rate_pct_per_min=trend_rate,
            severity=severity,
            projected_time_to_threshold_min=projected_time,
            projected_peak_pct=projected_peak,
            current_count=reading.count,
            capacity=reading.capacity,
            timestamp=reading.timestamp,
        )

    def get_all_zone_analyses(self) -> list[TrendAnalysis]:
        """Get the latest trend analysis for all tracked zones."""
        analyses: list[TrendAnalysis] = []
        for zone_id, readings in self._readings.items():
            if not readings:
                continue
            latest = readings[-1]
            trend_rate = self._compute_trend_rate(readings)
            trend_direction = self._classify_trend(trend_rate)
            severity = self._classify_severity(latest.density_pct)
            projected_time = self._project_time_to_threshold(
                latest.density_pct, trend_rate, severity
            )
            projected_peak = self._project_peak(latest.density_pct, trend_rate)

            analyses.append(
                TrendAnalysis(
                    zone_id=zone_id,
                    zone_name=self._zone_names.get(zone_id, f"Zone-{zone_id[:8]}"),
                    current_density_pct=latest.density_pct,
                    ewma_density_pct=self._ewma[zone_id],
                    trend_direction=trend_direction,
                    trend_rate_pct_per_min=trend_rate,
                    severity=severity,
                    projected_time_to_threshold_min=projected_time,
                    projected_peak_pct=projected_peak,
                    current_count=latest.count,
                    capacity=latest.capacity,
                    timestamp=latest.timestamp,
                )
            )
        return analyses

    def classify_severity(self, density_pct: float) -> SeverityLevel:
        """Public method to classify severity for a given density percentage."""
        return self._classify_severity(density_pct)

    def _classify_severity(self, density_pct: float) -> SeverityLevel:
        """Classify density into severity levels based on thresholds."""
        if density_pct >= self.THRESHOLD_EMERGENCY:
            return SeverityLevel.EMERGENCY
        if density_pct >= self.THRESHOLD_CRITICAL:
            return SeverityLevel.CRITICAL
        if density_pct >= self.THRESHOLD_WARNING:
            return SeverityLevel.WARNING
        return SeverityLevel.NORMAL

    def _classify_trend(self, rate_pct_per_min: float) -> str:
        """Classify trend direction based on rate of change."""
        if rate_pct_per_min > self.TREND_STABLE_THRESHOLD:
            return "rising"
        if rate_pct_per_min < -self.TREND_STABLE_THRESHOLD:
            return "falling"
        return "stable"

    def _compute_trend_rate(self, readings: list[DensityReading]) -> float:
        """Compute the rate of density change in pct/minute using linear regression.

        Uses the last 12 readings (1 minute at 5s intervals) for trend computation.
        """
        if len(readings) < 2:
            return 0.0

        # Use last 12 readings (1 minute window)
        recent = readings[-12:]
        if len(recent) < 2:
            return 0.0

        # Simple linear regression: y = density_pct, x = time_in_seconds
        base_time = recent[0].timestamp
        n = len(recent)

        sum_x = 0.0
        sum_y = 0.0
        sum_xy = 0.0
        sum_x2 = 0.0

        for reading in recent:
            x = (reading.timestamp - base_time).total_seconds()
            y = reading.density_pct
            sum_x += x
            sum_y += y
            sum_xy += x * y
            sum_x2 += x * x

        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return 0.0

        # Slope in pct/second
        slope = (n * sum_xy - sum_x * sum_y) / denominator

        # Convert to pct/minute
        return slope * 60.0

    def _project_time_to_threshold(
        self,
        current_pct: float,
        rate_pct_per_min: float,
        current_severity: SeverityLevel,
    ) -> float | None:
        """Project time until the next severity threshold is crossed.

        Returns minutes until next threshold, or None if trend is stable/falling.
        """
        if rate_pct_per_min <= self.TREND_STABLE_THRESHOLD:
            return None  # Not rising

        # Determine next threshold
        if current_severity == SeverityLevel.NORMAL:
            next_threshold = self.THRESHOLD_WARNING
        elif current_severity == SeverityLevel.WARNING:
            next_threshold = self.THRESHOLD_CRITICAL
        elif current_severity == SeverityLevel.CRITICAL:
            next_threshold = self.THRESHOLD_EMERGENCY
        else:
            return None  # Already at emergency

        remaining_pct = next_threshold - current_pct
        if remaining_pct <= 0:
            return 0.0

        return remaining_pct / rate_pct_per_min

    def _project_peak(
        self,
        current_pct: float,
        rate_pct_per_min: float,
    ) -> float | None:
        """Project peak density assuming current trend continues for 15 minutes."""
        if rate_pct_per_min <= self.TREND_STABLE_THRESHOLD:
            return None
        projected = current_pct + rate_pct_per_min * 15.0
        return min(projected, 100.0)
