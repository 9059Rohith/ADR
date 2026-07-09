"""SentinelArena — Unit Tests for Density Evaluator.

Tests the deterministic EWMA-based crowd density analysis,
severity classification, and time-to-threshold projection.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.density_evaluator import (
    DensityEvaluator,
    DensityReading,
    SeverityLevel,
)


@pytest.fixture
def evaluator() -> DensityEvaluator:
    """Create a density evaluator with a registered test zone."""
    ev = DensityEvaluator()
    ev.register_zone("zone-test", "Test Zone")
    return ev


class TestDensityEvaluator:
    """Tests for the EWMA density evaluator."""

    def test_severity_classification(self, evaluator: DensityEvaluator) -> None:
        """Test severity levels at threshold boundaries."""
        assert evaluator.classify_severity(50.0) == SeverityLevel.NORMAL
        assert evaluator.classify_severity(74.9) == SeverityLevel.NORMAL
        assert evaluator.classify_severity(75.0) == SeverityLevel.WARNING
        assert evaluator.classify_severity(84.9) == SeverityLevel.WARNING
        assert evaluator.classify_severity(85.0) == SeverityLevel.CRITICAL
        assert evaluator.classify_severity(94.9) == SeverityLevel.CRITICAL
        assert evaluator.classify_severity(95.0) == SeverityLevel.EMERGENCY
        assert evaluator.classify_severity(100.0) == SeverityLevel.EMERGENCY

    def test_single_reading(self, evaluator: DensityEvaluator) -> None:
        """Test adding a single reading."""
        reading = DensityReading(
            zone_id="zone-test",
            count=300,
            capacity=500,
            timestamp=datetime.now(UTC),
        )
        analysis = evaluator.add_reading(reading)

        assert analysis.zone_id == "zone-test"
        assert analysis.zone_name == "Test Zone"
        assert analysis.current_density_pct == 60.0
        assert analysis.severity == SeverityLevel.NORMAL
        assert analysis.current_count == 300
        assert analysis.capacity == 500

    def test_rising_trend(self, evaluator: DensityEvaluator) -> None:
        """Test that rising density is detected."""
        base_time = datetime.now(UTC)

        for i in range(15):
            reading = DensityReading(
                zone_id="zone-test",
                count=200 + i * 10,  # Rising from 200 to 340
                capacity=500,
                timestamp=base_time + timedelta(seconds=i * 5),
            )
            analysis = evaluator.add_reading(reading)

        assert analysis.trend_direction == "rising"
        assert analysis.trend_rate_pct_per_min > 0

    def test_falling_trend(self, evaluator: DensityEvaluator) -> None:
        """Test that falling density is detected."""
        base_time = datetime.now(UTC)

        for i in range(15):
            reading = DensityReading(
                zone_id="zone-test",
                count=400 - i * 10,  # Falling from 400 to 260
                capacity=500,
                timestamp=base_time + timedelta(seconds=i * 5),
            )
            analysis = evaluator.add_reading(reading)

        assert analysis.trend_direction == "falling"
        assert analysis.trend_rate_pct_per_min < 0

    def test_stable_trend(self, evaluator: DensityEvaluator) -> None:
        """Test that stable density is detected."""
        base_time = datetime.now(UTC)

        for i in range(15):
            reading = DensityReading(
                zone_id="zone-test",
                count=250,  # Constant
                capacity=500,
                timestamp=base_time + timedelta(seconds=i * 5),
            )
            analysis = evaluator.add_reading(reading)

        assert analysis.trend_direction == "stable"

    def test_ewma_smoothing(self, evaluator: DensityEvaluator) -> None:
        """Test that EWMA smooths out spikes."""
        base_time = datetime.now(UTC)

        # Add steady readings
        for i in range(10):
            reading = DensityReading(
                zone_id="zone-test",
                count=250,
                capacity=500,
                timestamp=base_time + timedelta(seconds=i * 5),
            )
            evaluator.add_reading(reading)

        # Add a spike
        spike_reading = DensityReading(
            zone_id="zone-test",
            count=450,
            capacity=500,
            timestamp=base_time + timedelta(seconds=50),
        )
        analysis = evaluator.add_reading(spike_reading)

        # EWMA should be between the steady-state and the spike
        assert analysis.ewma_density_pct < analysis.current_density_pct
        assert analysis.ewma_density_pct > 50.0  # Above steady state

    def test_time_to_threshold_projection(self, evaluator: DensityEvaluator) -> None:
        """Test time-to-threshold projection for rising trends."""
        base_time = datetime.now(UTC)

        # Create rising trend approaching warning threshold
        for i in range(15):
            count = 300 + i * 5  # Rising steadily
            reading = DensityReading(
                zone_id="zone-test",
                count=count,
                capacity=500,
                timestamp=base_time + timedelta(seconds=i * 5),
            )
            analysis = evaluator.add_reading(reading)

        # If rising and below threshold, should have a projection
        if analysis.trend_direction == "rising" and analysis.severity == SeverityLevel.NORMAL:
            assert analysis.projected_time_to_threshold_min is not None
            assert analysis.projected_time_to_threshold_min > 0

    def test_serialization(self, evaluator: DensityEvaluator) -> None:
        """Test that analysis serializes correctly (grounding boundary)."""
        reading = DensityReading(
            zone_id="zone-test",
            count=400,
            capacity=500,
            timestamp=datetime.now(UTC),
        )
        analysis = evaluator.add_reading(reading)
        data = analysis.to_dict()

        # Verify all required fields for LLM consumption
        assert "zone_id" in data
        assert "zone_name" in data
        assert "current_density_pct" in data
        assert "severity" in data
        assert "trend_direction" in data
        assert isinstance(data["current_density_pct"], float)
        assert data["severity"] in ("normal", "warning", "critical", "emergency")

    def test_multiple_zones(self) -> None:
        """Test tracking multiple zones simultaneously."""
        ev = DensityEvaluator()
        ev.register_zone("zone-a", "Zone A")
        ev.register_zone("zone-b", "Zone B")

        now = datetime.now(UTC)
        ev.add_reading(DensityReading("zone-a", 200, 500, now))
        ev.add_reading(DensityReading("zone-b", 400, 500, now))

        analyses = ev.get_all_zone_analyses()
        assert len(analyses) == 2

        zone_a = next(a for a in analyses if a.zone_id == "zone-a")
        zone_b = next(a for a in analyses if a.zone_id == "zone-b")
        assert zone_a.current_density_pct == 40.0
        assert zone_b.current_density_pct == 80.0

    def test_density_capped_at_100(self, evaluator: DensityEvaluator) -> None:
        """Test that density percentage never exceeds 100%."""
        reading = DensityReading(
            zone_id="zone-test",
            count=600,  # Over capacity
            capacity=500,
            timestamp=datetime.now(UTC),
        )
        assert reading.density_pct == 100.0

    def test_actionable_determination(self, evaluator: DensityEvaluator) -> None:
        """Test the is_actionable property."""
        # High density reading should be actionable
        reading = DensityReading(
            zone_id="zone-test",
            count=400,
            capacity=500,
            timestamp=datetime.now(UTC),
        )
        analysis = evaluator.add_reading(reading)
        assert analysis.severity == SeverityLevel.WARNING
        assert analysis.is_actionable is True

    def test_sliding_window_trim(self, evaluator: DensityEvaluator) -> None:
        """Test that the sliding window trims old readings."""
        base_time = datetime.now(UTC)

        # Add more readings than MAX_READINGS
        for i in range(150):
            reading = DensityReading(
                zone_id="zone-test",
                count=250,
                capacity=500,
                timestamp=base_time + timedelta(seconds=i * 5),
            )
            evaluator.add_reading(reading)

        # Should have trimmed to MAX_READINGS
        assert len(evaluator._readings["zone-test"]) <= evaluator.MAX_READINGS
