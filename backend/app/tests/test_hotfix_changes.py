"""
Tests for the hotfix changes - analytics summary no-data handling and group API improvements.
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.db.repositories import LLMAuditRepository
from app.schemas.dto import LocationGroupBulkMembershipRequest, AnalyticsSummaryRequest
from app.analytics.services.summary_prompt_service import SummaryPromptService


class TestLLMAuditRepository:
    """Test LLMAudit repository with new columns."""

    @pytest.mark.asyncio
    async def test_record_with_feature_flags(self):
        """Test that LLMAudit record accepts new feature flag columns."""
        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        repo = LLMAuditRepository(mock_session)
        
        # Test with new feature flags
        audit = await repo.record(
            user_id=1,
            endpoint="test",
            model="gpt-4",
            prompt_summary="Test prompt",
            tokens_in=100,
            tokens_out=50,
            has_air_quality=True,
            has_astronomy=False
        )
        
        # Verify session was called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()


class TestLocationGroupBulkMembershipRequest:
    """Test bulk membership request schema."""
    
    def test_bulk_membership_request_valid(self):
        """Test valid bulk membership request."""
        request = LocationGroupBulkMembershipRequest(
            add=[1, 2, 3],
            remove=[4, 5]
        )
        
        assert request.add == [1, 2, 3]
        assert request.remove == [4, 5]
        
    def test_bulk_membership_request_empty(self):
        """Test empty bulk membership request."""
        request = LocationGroupBulkMembershipRequest()
        
        assert request.add == []
        assert request.remove == []


class TestAnalyticsSummaryNoData:
    """Test analytics summary no-data handling."""
    
    @pytest.mark.asyncio
    async def test_summary_prompt_service_no_data_detection(self):
        """Test that SummaryPromptService detects when there's no data."""
        # Mock session and repositories
        mock_session = AsyncMock()
        
        service = SummaryPromptService(mock_session)
        
        # Mock empty data responses
        service.trend_repo.get_by_location_and_metrics = AsyncMock(return_value=[])
        service.aggregation_repo.get_by_location_and_period = AsyncMock(return_value=[])
        service.accuracy_repo.get_by_location_and_period = AsyncMock(return_value=[])
        
        # Build prompt for location with no data
        prompt_data = await service.build_analytics_prompt(
            location_id=999,
            period='7d',
            metrics=['avg_temp_c']
        )
        
        # Verify no-data detection
        assert prompt_data['metadata']['total_data_points'] == 0
        assert prompt_data['metadata']['has_sufficient_data'] is False
        assert len(prompt_data['trends']) == 0
        assert len(prompt_data['recent_daily_data']) == 0


class TestAnalyticsSummaryRequest:
    """Test analytics summary request schema."""
    
    def test_analytics_summary_request_valid(self):
        """Test valid analytics summary request."""
        request = AnalyticsSummaryRequest(
            location_id=1,
            period="7d",
            metrics=["avg_temp_c", "total_precip_mm"]
        )
        
        assert request.location_id == 1
        assert request.period == "7d"
        assert request.metrics == ["avg_temp_c", "total_precip_mm"]
        
    def test_analytics_summary_request_defaults(self):
        """Test analytics summary request with defaults."""
        request = AnalyticsSummaryRequest(location_id=1)
        
        assert request.location_id == 1
        assert request.period == "7d"
        assert request.metrics == ["avg_temp_c", "total_precip_mm", "max_wind_kph"]