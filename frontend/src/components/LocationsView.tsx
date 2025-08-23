import React, { useState, useEffect } from 'react';
import { Location, LocationCreate, ExplainResponse } from '../types/api';
import api from '../services/apiClient';

const LocationsView: React.FC = () => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newLocation, setNewLocation] = useState<LocationCreate>({
    name: '',
    lat: 0,
    lon: 0,
    timezone: 'UTC'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [explainLoading, setExplainLoading] = useState(false);

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      const response = await api.get<Location[]>('/v1/locations');
      setLocations(response.data);
    } catch (err: any) {
      setError('Failed to fetch locations');
    }
  };

  const handleAddLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post<Location>('/v1/locations', newLocation);
      setLocations([...locations, response.data]);
      setNewLocation({ name: '', lat: 0, lon: 0, timezone: 'UTC' });
      setShowAddForm(false);
    } catch (err: any) {
      setError(err.data?.detail || 'Failed to add location');
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async (locationId: number) => {
    setExplainLoading(true);
    setError('');
    setExplanation(null);

    try {
      const response = await api.post<ExplainResponse>(`/v1/locations/${locationId}/explain`);
      setExplanation(response.data);
    } catch (err: any) {
      setError(err.data?.detail || 'Failed to generate explanation');
    } finally {
      setExplainLoading(false);
    }
  };

  return (
    <div className="locations-container">
      <div className="locations-header">
        <h2>My Locations</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="add-button"
          disabled={loading}
        >
          {showAddForm ? 'Cancel' : 'Add Location'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {showAddForm && (
        <div className="add-location-form">
          <h3>Add New Location</h3>
          <form onSubmit={handleAddLocation}>
            <div className="form-group">
              <label htmlFor="name">Name:</label>
              <input
                type="text"
                id="name"
                value={newLocation.name}
                onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })}
                placeholder="e.g., Home, Office, Seattle"
                required
                disabled={loading}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="lat">Latitude:</label>
                <input
                  type="number"
                  id="lat"
                  value={newLocation.lat}
                  onChange={(e) => setNewLocation({ ...newLocation, lat: parseFloat(e.target.value) })}
                  step="any"
                  min="-90"
                  max="90"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="lon">Longitude:</label>
                <input
                  type="number"
                  id="lon"
                  value={newLocation.lon}
                  onChange={(e) => setNewLocation({ ...newLocation, lon: parseFloat(e.target.value) })}
                  step="any"
                  min="-180"
                  max="180"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="timezone">Timezone:</label>
              <select
                id="timezone"
                value={newLocation.timezone}
                onChange={(e) => setNewLocation({ ...newLocation, timezone: e.target.value })}
                disabled={loading}
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Chicago">Central Time</option>
                <option value="America/Denver">Mountain Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
                <option value="Europe/London">London</option>
                <option value="Europe/Paris">Paris</option>
                <option value="Asia/Tokyo">Tokyo</option>
              </select>
            </div>

            <button type="submit" disabled={loading} className="submit-button">
              {loading ? 'Adding...' : 'Add Location'}
            </button>
          </form>
        </div>
      )}

      <div className="locations-list">
        {locations.length === 0 ? (
          <p>No locations added yet. Add your first location to get started!</p>
        ) : (
          locations.map((location) => (
            <div key={location.id} className="location-card">
              <div className="location-info">
                <h3>{location.name}</h3>
                <p>Lat: {location.lat.toFixed(4)}, Lon: {location.lon.toFixed(4)}</p>
                <p>Timezone: {location.timezone || 'Not specified'}</p>
                <p>Added: {new Date(location.created_at).toLocaleDateString()}</p>
              </div>
              <div className="location-actions">
                <button
                  onClick={() => handleExplain(location.id)}
                  disabled={explainLoading}
                  className="explain-button"
                >
                  {explainLoading ? 'Generating...' : 'Explain Weather'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {explanation && (
        <div className="explanation-panel">
          <h3>Weather Explanation</h3>
          <div className="explanation-content">
            <div className="summary">
              <h4>Summary</h4>
              <p>{explanation.summary}</p>
            </div>

            <div className="actions">
              <h4>Recommended Actions</h4>
              <ul>
                {explanation.actions.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ul>
            </div>

            <div className="driver">
              <h4>Weather Driver</h4>
              <p>{explanation.driver}</p>
            </div>

            <div className="metadata">
              <small>
                Model: {explanation.model} | 
                Tokens: {explanation.tokens_in} in, {explanation.tokens_out} out
              </small>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LocationsView;