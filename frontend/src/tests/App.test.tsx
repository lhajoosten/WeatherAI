import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';


import App from '../App';

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    // Since we redirect to /locations by default, check for the locations page
    expect(screen.getByText('Locations Management')).toBeInTheDocument();
  });

  it('displays the locations page by default', () => {
    render(<App />);
    expect(screen.getByText('Route: /locations')).toBeInTheDocument();
  });
});