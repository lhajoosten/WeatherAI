"""Tests for ingestion orchestrator improvements."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from app.ingest.orchestrator import IngestionOrchestrator
from app.core.config import settings


class TestIngestionOrchestrator:
    """Test ingestion orchestrator with new stabilization features."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock async session."""
        return AsyncMock()
    
    @pytest.fixture
    def orchestrator(self, mock_session):
        """Create orchestrator with mocked dependencies."""
        return IngestionOrchestrator(mock_session)
    
    @pytest.mark.asyncio
    async def test_run_ingestion_cycle_skips_in_dev_when_disabled(self, orchestrator):
        """Test that ingestion is skipped in development when disabled."""
        # Mock settings to enable dev skip
        with patch.object(settings, 'app_env', 'development'), \
             patch.object(settings, 'disable_ingest_in_dev', True):
            
            result = await orchestrator.run_ingestion_cycle([1, 2, 3])
            
            assert result["skipped"] is True
            assert result["reason"] == "Disabled in development"
            assert result["total_locations"] == 3
            assert result["successful_locations"] == 0
            assert result["failed_locations"] == 0
    
    @pytest.mark.asyncio
    async def test_run_ingestion_cycle_proceeds_when_enabled_in_dev(self, orchestrator):
        """Test that ingestion proceeds when enabled in development."""
        # Mock settings to allow dev ingestion
        with patch.object(settings, 'app_env', 'development'), \
             patch.object(settings, 'disable_ingest_in_dev', False), \
             patch.object(orchestrator, '_ingest_location') as mock_ingest:
            
            # Mock successful location ingestion
            mock_ingest.return_value = {
                "location_id": 1,
                "tasks_completed": 4,
                "tasks_failed": 0,
                "no_data_tasks": 0,
                "errors": []
            }
            
            result = await orchestrator.run_ingestion_cycle([1])
            
            assert "skipped" not in result
            assert result["successful_locations"] == 1
            assert result["tasks_completed"] == 4
            assert mock_ingest.called
    
    @pytest.mark.asyncio
    async def test_run_ingestion_cycle_proceeds_in_production(self, orchestrator):
        """Test that ingestion proceeds in production regardless of flag."""
        # Mock settings for production
        with patch.object(settings, 'app_env', 'production'), \
             patch.object(settings, 'disable_ingest_in_dev', True), \
             patch.object(orchestrator, '_ingest_location') as mock_ingest:
            
            # Mock successful location ingestion
            mock_ingest.return_value = {
                "location_id": 1,
                "tasks_completed": 4,
                "tasks_failed": 0,
                "no_data_tasks": 0,
                "errors": []
            }
            
            result = await orchestrator.run_ingestion_cycle([1])
            
            assert "skipped" not in result
            assert result["successful_locations"] == 1
            assert mock_ingest.called
    
    @pytest.mark.asyncio
    async def test_ingest_location_handles_no_data_response(self, orchestrator):
        """Test that NO_DATA response from air quality is handled correctly."""
        location_id = 123
        lat, lon = 40.7128, -74.0060
        
        # Mock all provider methods
        with patch.object(orchestrator, '_fetch_forecast') as mock_forecast, \
             patch.object(orchestrator, '_fetch_observations') as mock_obs, \
             patch.object(orchestrator, '_fetch_air_quality') as mock_air, \
             patch.object(orchestrator, '_compute_astronomy') as mock_astro:
            
            # Mock air quality returning NO_DATA
            mock_forecast.return_value = None
            mock_obs.return_value = None
            mock_air.return_value = "NO_DATA"
            mock_astro.return_value = None
            
            result = await orchestrator._ingest_location(location_id, lat, lon)
            
            assert result["tasks_completed"] == 3
            assert result["tasks_failed"] == 0
            assert result["no_data_tasks"] == 1
            assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_air_quality_provider_empty_response_handled(self, orchestrator):
        """Test that empty air quality response is handled as NO_DATA."""
        location_id = 123
        lat, lon = 40.7128, -74.0060
        
        # Mock provider run repository
        mock_provider_run = AsyncMock()
        mock_provider_run.id = 456
        orchestrator.provider_run_repo.create = AsyncMock(return_value=mock_provider_run)
        orchestrator.provider_run_repo.update_status = AsyncMock()
        
        # Mock air quality provider returning empty list (404 handled)
        orchestrator.air_quality_provider.fetch_air_quality = AsyncMock(return_value=[])
        
        result = await orchestrator._fetch_air_quality(location_id, lat, lon)
        
        assert result == "NO_DATA"
        
        # Verify provider run was updated with NO_DATA status
        orchestrator.provider_run_repo.update_status.assert_called_once_with(
            run_id=456,
            status="NO_DATA",
            records_ingested=0
        )
    
    @pytest.mark.asyncio
    async def test_air_quality_provider_success_response(self, orchestrator):
        """Test that successful air quality response is handled correctly."""
        location_id = 123
        lat, lon = 40.7128, -74.0060
        
        # Mock provider run repository
        mock_provider_run = AsyncMock()
        mock_provider_run.id = 456
        orchestrator.provider_run_repo.create = AsyncMock(return_value=mock_provider_run)
        orchestrator.provider_run_repo.update_status = AsyncMock()
        
        # Mock air quality provider returning data
        mock_records = [{"location_id": 123, "pm2_5": 15.0}]
        orchestrator.air_quality_provider.fetch_air_quality = AsyncMock(return_value=mock_records)
        orchestrator.air_quality_repo.bulk_upsert = AsyncMock(return_value=1)
        
        result = await orchestrator._fetch_air_quality(location_id, lat, lon)
        
        assert result is None  # Success returns None
        
        # Verify provider run was updated with SUCCESS status
        orchestrator.provider_run_repo.update_status.assert_called_once_with(
            run_id=456,
            status="SUCCESS",
            records_ingested=1
        )
    
    @pytest.mark.asyncio
    async def test_error_message_truncation(self, orchestrator):
        """Test that error messages are truncated properly."""
        location_id = 123
        lat, lon = 40.7128, -74.0060
        
        # Mock provider run repository
        mock_provider_run = AsyncMock()
        mock_provider_run.id = 456
        orchestrator.provider_run_repo.create = AsyncMock(return_value=mock_provider_run)
        orchestrator.provider_run_repo.update_status = AsyncMock()
        
        # Mock air quality provider raising a long error
        long_error = "A" * 600  # 600 character error message
        orchestrator.air_quality_provider.fetch_air_quality = AsyncMock(side_effect=Exception(long_error))
        
        with pytest.raises(Exception):
            await orchestrator._fetch_air_quality(location_id, lat, lon)
        
        # Verify error message was truncated
        call_args = orchestrator.provider_run_repo.update_status.call_args[1]
        assert len(call_args["error_message"]) == 500
        assert call_args["error_message"].endswith("...")
        assert call_args["status"] == "FAILED"