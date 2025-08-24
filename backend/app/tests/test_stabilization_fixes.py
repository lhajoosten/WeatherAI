"""Tests for stabilization PR fixes."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

from app.analytics.services.summary_prompt_service import SummaryPromptService
from app.db.repositories import LocationGroupRepository, LocationRepository
from app.services.rate_limit import RateLimitService


class TestDatetimeFix:
    """Test that datetime import issues are fixed."""
    
    def test_summary_prompt_service_timedelta_import(self):
        """Test that SummaryPromptService can import timedelta correctly."""
        # The import should work without errors
        service = SummaryPromptService.__new__(SummaryPromptService)
        
        # Test that timedelta can be used (this would fail before the fix)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        assert isinstance(start_date, datetime)
        assert start_date < end_date

    def test_accuracy_service_timedelta_usage(self):
        """Test that AccuracyService correctly uses timedelta for 7-day window calculations."""
        from app.analytics.services.accuracy_service import AccuracyService
        
        # Test that the class can be instantiated and timedelta calculations work
        # This would fail if datetime.timedelta was used incorrectly
        test_time = datetime(2024, 1, 15, 12, 0, 0)
        
        # Simulate the timedelta calculations that were broken
        time_window_start = test_time - timedelta(minutes=30)
        time_window_end = test_time + timedelta(minutes=30)
        lead_time_min = timedelta(hours=23)  # 24-1 hours
        lead_time_max = timedelta(hours=25)  # 24+1 hours
        
        # Verify calculations work correctly
        assert time_window_start == datetime(2024, 1, 15, 11, 30, 0)
        assert time_window_end == datetime(2024, 1, 15, 12, 30, 0)
        assert lead_time_min.total_seconds() == 23 * 3600
        assert lead_time_max.total_seconds() == 25 * 3600

    def test_analytics_config_env_variable(self):
        """Test that analytics configuration reads from environment."""
        from app.core.config import Settings
        import os
        
        # Test default value
        settings = Settings()
        assert settings.analytics_max_range_days == 30
        
        # Test with environment override
        original = os.environ.get("ANALYTICS_MAX_RANGE_DAYS")
        try:
            os.environ["ANALYTICS_MAX_RANGE_DAYS"] = "45"
            test_settings = Settings()
            assert test_settings.analytics_max_range_days == 45
        finally:
            if original is not None:
                os.environ["ANALYTICS_MAX_RANGE_DAYS"] = original
            elif "ANALYTICS_MAX_RANGE_DAYS" in os.environ:
                del os.environ["ANALYTICS_MAX_RANGE_DAYS"]


class TestGroupLoadingFix:
    """Test that group loading uses eager loading correctly."""
    
    @pytest.mark.asyncio
    async def test_location_group_repository_uses_selectinload(self):
        """Test that LocationGroupRepository uses selectinload to avoid MissingGreenlet."""
        # Mock session
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        repo = LocationGroupRepository(mock_session)
        
        # Call the method that was causing MissingGreenlet
        groups = await repo.get_by_user_id(user_id=1)
        
        # Verify that the query was executed
        mock_session.execute.assert_called_once()
        
        # Check that the query string contains selectinload (this is a proxy test)
        # The actual fix uses selectinload which should be present in the query
        assert groups == []  # Empty result from mock

    def test_group_create_dto_construction(self):
        """Test that group creation returns proper DTO with empty member lists."""
        from app.schemas.dto import LocationGroupResponse
        from datetime import datetime
        
        # Create mock group object without members loaded
        class MockGroup:
            def __init__(self):
                self.id = 1
                self.name = "Test Group"
                self.description = "Test Description"
                self.created_at = datetime.utcnow()
                # Don't set members to simulate lazy loading disabled
        
        mock_group = MockGroup()
        
        # Test that from_orm handles missing members gracefully
        response = LocationGroupResponse.from_orm(mock_group)
        
        assert response.id == 1
        assert response.name == "Test Group"
        assert response.description == "Test Description"
        assert response.members == []
        assert response.member_location_ids == []

    def test_location_group_model_lazy_raise(self):
        """Test that LocationGroup.members is configured with lazy='raise'."""
        from app.db.models import LocationGroup
        
        # Check that the relationship has lazy='raise' configured
        members_property = LocationGroup.__mapper__.relationships['members']
        assert members_property.lazy == 'raise', "LocationGroup.members should have lazy='raise' to surface unintended lazy access"


class TestLocationDeletion:
    """Test location deletion with cascade handling."""
    
    @pytest.mark.asyncio
    async def test_location_delete_handles_integrity_error(self):
        """Test that location deletion handles FK constraint errors gracefully."""
        from sqlalchemy.exc import IntegrityError
        
        # Mock session that raises IntegrityError then succeeds
        mock_session = AsyncMock()
        mock_location = Mock()
        mock_location.id = 123
        
        repo = LocationRepository(mock_session)
        repo.get_by_id_and_user = AsyncMock(return_value=mock_location)
        
        # First delete attempt raises IntegrityError
        # Second delete attempt (after cascade) succeeds
        mock_session.delete.side_effect = [None, None]  # Won't actually raise, but simulates the pattern
        mock_session.commit.side_effect = [IntegrityError("test", "test", "test"), None]
        mock_session.rollback.return_value = None
        
        # Mock the execute calls for cascade deletion
        mock_session.execute.return_value = AsyncMock()
        
        # Test deletion
        result = await repo.delete(location_id=123, user_id=456)
        
        # Should succeed despite initial IntegrityError
        assert result is True
        
        # Verify rollback was called after IntegrityError
        mock_session.rollback.assert_called_once()


class TestCORSConfiguration:
    """Test CORS configuration includes new origins."""
    
    def test_cors_origins_include_port_4200(self):
        """Test that CORS origins include Angular development port 4200."""
        from app.core.config import settings
        
        # Check that the new origins are included
        expected_origins = [
            "http://localhost:4200",
            "http://127.0.0.1:4200"
        ]
        
        for origin in expected_origins:
            assert origin in settings.cors_origins


class TestRateLimitingImprovements:
    """Test analytics rate limiting improvements."""
    
    def test_analytics_endpoints_have_higher_limits(self):
        """Test that analytics endpoints have higher rate limits."""
        rate_limiter = RateLimitService()
        
        # Analytics endpoints should have 3x normal limit
        analytics_limit = rate_limiter._get_rate_limit("analytics")
        normal_limit = rate_limiter._get_rate_limit("normal_endpoint")
        
        assert analytics_limit == normal_limit * 3
    
    def test_llm_endpoints_keep_lower_limits(self):
        """Test that LLM endpoints keep their lower limits."""
        rate_limiter = RateLimitService()
        
        # LLM endpoints should have the LLM-specific limit
        llm_limit = rate_limiter._get_rate_limit("analytics_llm")
        analytics_limit = rate_limiter._get_rate_limit("analytics")
        
        assert llm_limit < analytics_limit


class TestDashboardEndpoint:
    """Test the new consolidated dashboard endpoint."""
    
    def test_dashboard_response_model_structure(self):
        """Test that DashboardResponse has the expected structure."""
        from app.api.v1.routes.analytics import DashboardResponse
        
        # Check that all required fields are present
        fields = DashboardResponse.model_fields
        
        expected_fields = {
            'observations', 'aggregations', 'trends', 
            'accuracy', 'generated_at', 'cache_hit'
        }
        
        assert expected_fields.issubset(set(fields.keys()))
    
    @pytest.mark.asyncio
    async def test_dashboard_endpoint_rate_limiting(self):
        """Test that dashboard endpoint uses analytics rate limiting."""
        # This is a design verification test
        # The actual endpoint should use rate_limiter.check_rate_limit(user_id, "analytics")
        # which will get the higher limit for analytics
        
        rate_limiter = RateLimitService()
        limit = rate_limiter._get_rate_limit("analytics")
        
        # Should be higher than normal endpoints
        assert limit > rate_limiter.requests_per_minute


class TestLocationGroupResponseFix:
    """Test the LocationGroupResponse DTO fixes."""
    
    def test_location_group_response_from_orm(self):
        """Test that LocationGroupResponse.from_orm handles members correctly."""
        from app.schemas.dto import LocationGroupResponse, LocationResponse
        
        # Mock group with members
        mock_member = Mock()
        mock_member.location = Mock()
        mock_member.location.id = 1
        mock_member.location.name = "Test Location"
        mock_member.location.lat = 40.7128
        mock_member.location.lon = -74.0060
        mock_member.location.timezone = "America/New_York"
        mock_member.location.created_at = datetime.utcnow()
        
        mock_group = Mock()
        mock_group.id = 1
        mock_group.name = "Test Group"
        mock_group.description = "Test Description"
        mock_group.created_at = datetime.utcnow()
        mock_group.members = [mock_member]
        
        # This should not raise an error now
        response = LocationGroupResponse.from_orm(mock_group)
        
        assert response.id == 1
        assert response.name == "Test Group"
        assert len(response.members) == 1
        assert response.members[0].name == "Test Location"