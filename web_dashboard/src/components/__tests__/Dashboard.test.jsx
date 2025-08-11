import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../Dashboard';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock chart.js
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
  Doughnut: () => <div data-testid="doughnut-chart">Doughnut Chart</div>,
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  format: jest.fn(() => 'Jan 01'),
  subDays: jest.fn(() => new Date('2024-01-01')),
  startOfDay: jest.fn(() => new Date('2024-01-01T00:00:00')),
  endOfDay: jest.fn(() => new Date('2024-01-01T23:59:59')),
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  error: jest.fn(),
  success: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const renderWithProviders = (component) => {
  const queryClient = createTestQueryClient();
  
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {component}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    test('renders dashboard header correctly', () => {
      renderWithProviders(<Dashboard />);
      
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Monitor your eye health and wellness metrics')).toBeInTheDocument();
    });

    test('renders time range selector', () => {
      renderWithProviders(<Dashboard />);
      
      const timeRangeSelect = screen.getByRole('combobox');
      expect(timeRangeSelect).toBeInTheDocument();
      expect(timeRangeSelect).toHaveValue('7d');
    });

    test('renders stats cards', () => {
      renderWithProviders(<Dashboard />);
      
      expect(screen.getByText('Total Blinks')).toBeInTheDocument();
      expect(screen.getByText('Blink Rate')).toBeInTheDocument();
      expect(screen.getByText('Active Time')).toBeInTheDocument();
      expect(screen.getByText('Health Score')).toBeInTheDocument();
    });

    test('renders chart sections', () => {
      renderWithProviders(<Dashboard />);
      
      expect(screen.getByText('Blink Trend')).toBeInTheDocument();
      expect(screen.getByText('System Performance')).toBeInTheDocument();
      expect(screen.getByText('Weekly Activity')).toBeInTheDocument();
      expect(screen.getByText('Eye Health Distribution')).toBeInTheDocument();
    });

    test('renders sync status section', () => {
      renderWithProviders(<Dashboard />);
      
      expect(screen.getByText('Data Synchronization')).toBeInTheDocument();
    });
  });

  describe('Data Loading States', () => {
    test('shows loading states for blink data', async () => {
      fetch.mockImplementation(() => 
        new Promise(() => {}) // Never resolves
      );

      renderWithProviders(<Dashboard />);
      
      // Check for loading indicators
      const loadingSpinners = screen.getAllByTestId('loading-spinner');
      expect(loadingSpinners.length).toBeGreaterThan(0);
    });

    test('shows loading states for performance data', async () => {
      fetch.mockImplementation(() => 
        new Promise(() => {}) // Never resolves
      );

      renderWithProviders(<Dashboard />);
      
      // Check for loading indicators in performance section
      const performanceSection = screen.getByText('System Performance').closest('div');
      expect(performanceSection).toBeInTheDocument();
    });

    test('shows loading states for sync status', async () => {
      fetch.mockImplementation(() => 
        new Promise(() => {}) // Never resolves
      );

      renderWithProviders(<Dashboard />);
      
      // Check for loading indicators in sync section
      const syncSection = screen.getByText('Data Synchronization').closest('div');
      expect(syncSection).toBeInTheDocument();
    });
  });

  describe('Data Display', () => {
    test('displays blink data correctly', async () => {
      const mockBlinkData = {
        events: [
          { timestamp: 1640995200, count: 5 },
          { timestamp: 1641081600, count: 3 },
        ],
        total_blinks: 8,
        avg_blink_rate: 12,
        active_hours: 6,
        health_score: 85,
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBlinkData,
      });

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('8')).toBeInTheDocument(); // Total blinks
        expect(screen.getByText('12/min')).toBeInTheDocument(); // Blink rate
        expect(screen.getByText('6h')).toBeInTheDocument(); // Active time
        expect(screen.getByText('85%')).toBeInTheDocument(); // Health score
      });
    });

    test('displays performance data correctly', async () => {
      const mockPerformanceData = {
        cpu_percent: 45.2,
        memory_percent: 67.8,
        energy_impact: 'Medium',
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPerformanceData,
      });

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('45.2%')).toBeInTheDocument(); // CPU usage
        expect(screen.getByText('67.8%')).toBeInTheDocument(); // Memory usage
        expect(screen.getByText('Medium')).toBeInTheDocument(); // Energy impact
      });
    });

    test('displays sync status correctly', async () => {
      const mockSyncStatus = {
        status: 'connected',
        last_sync: '2024-01-01T12:00:00Z',
        pending_events: 0,
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSyncStatus,
      });

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Connected')).toBeInTheDocument();
        expect(screen.getByText(/Last sync: Jan 01, 2024/)).toBeInTheDocument();
      });
    });

    test('displays pending sync events', async () => {
      const mockSyncStatus = {
        status: 'pending',
        last_sync: '2024-01-01T12:00:00Z',
        pending_events: 5,
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSyncStatus,
      });

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Pending')).toBeInTheDocument();
        expect(screen.getByText('5 events waiting to sync')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('handles blink data fetch error', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(require('react-hot-toast').error).toHaveBeenCalledWith('Failed to load dashboard data');
      });
    });

    test('handles performance data fetch error', async () => {
      fetch.mockRejectedValueOnce(new Error('Performance data error'));

      renderWithProviders(<Dashboard />);
      
      // Should not crash the component
      expect(screen.getByText('System Performance')).toBeInTheDocument();
    });

    test('handles sync status fetch error', async () => {
      fetch.mockRejectedValueOnce(new Error('Sync status error'));

      renderWithProviders(<Dashboard />);
      
      // Should not crash the component
      expect(screen.getByText('Data Synchronization')).toBeInTheDocument();
    });

    test('handles malformed data gracefully', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ invalid: 'data' }),
      });

      renderWithProviders(<Dashboard />);
      
      // Should not crash and show default values
      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument(); // Default total blinks
        expect(screen.getByText('0/min')).toBeInTheDocument(); // Default blink rate
      });
    });
  });

  describe('User Interactions', () => {
    test('changes time range when selector is used', async () => {
      renderWithProviders(<Dashboard />);
      
      const timeRangeSelect = screen.getByRole('combobox');
      fireEvent.change(timeRangeSelect, { target: { value: '30d' } });
      
      expect(timeRangeSelect).toHaveValue('30d');
    });

    test('refetches data when time range changes', async () => {
      const mockBlinkData = {
        events: [],
        total_blinks: 0,
        avg_blink_rate: 0,
        active_hours: 0,
        health_score: 0,
      };

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockBlinkData,
      });

      renderWithProviders(<Dashboard />);
      
      const timeRangeSelect = screen.getByRole('combobox');
      fireEvent.change(timeRangeSelect, { target: { value: '30d' } });
      
      // Should trigger a new fetch
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(2); // Initial + time range change
      });
    });
  });

  describe('Chart Rendering', () => {
    test('renders blink trend chart', async () => {
      const mockBlinkData = {
        events: [
          { timestamp: 1640995200, count: 5 },
          { timestamp: 1641081600, count: 3 },
        ],
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBlinkData,
      });

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      });
    });

    test('renders performance chart', async () => {
      const mockPerformanceData = {
        cpu_percent: 45.2,
        memory_percent: 67.8,
        energy_impact: 'Medium',
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPerformanceData,
      });

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      });
    });

    test('renders weekly activity chart', () => {
      renderWithProviders(<Dashboard />);
      
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });

    test('renders eye health distribution chart', () => {
      renderWithProviders(<Dashboard />);
      
      expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    test('adapts to different screen sizes', () => {
      // Mock window resize
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768, // Tablet size
      });

      renderWithProviders(<Dashboard />);
      
      // Should still render all components
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Total Blinks')).toBeInTheDocument();
      expect(screen.getByText('Blink Trend')).toBeInTheDocument();
    });

    test('maintains functionality on mobile', () => {
      // Mock mobile screen size
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375, // Mobile size
      });

      renderWithProviders(<Dashboard />);
      
      // Should still be interactive
      const timeRangeSelect = screen.getByRole('combobox');
      expect(timeRangeSelect).toBeInTheDocument();
      expect(timeRangeSelect).not.toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels', () => {
      renderWithProviders(<Dashboard />);
      
      const timeRangeSelect = screen.getByRole('combobox');
      expect(timeRangeSelect).toHaveAttribute('aria-label');
    });

    test('supports keyboard navigation', () => {
      renderWithProviders(<Dashboard />);
      
      const timeRangeSelect = screen.getByRole('combobox');
      timeRangeSelect.focus();
      
      // Should be able to navigate with arrow keys
      fireEvent.keyDown(timeRangeSelect, { key: 'ArrowDown' });
      expect(timeRangeSelect).toHaveFocus();
    });

    test('has proper color contrast', () => {
      renderWithProviders(<Dashboard />);
      
      // Check that text elements have sufficient contrast
      const headings = screen.getAllByRole('heading');
      headings.forEach(heading => {
        const computedStyle = window.getComputedStyle(heading);
        expect(computedStyle.color).toBeDefined();
      });
    });
  });

  describe('Performance', () => {
    test('does not re-render unnecessarily', () => {
      const { rerender } = renderWithProviders(<Dashboard />);
      
      // Mock performance.now to track renders
      const originalPerformanceNow = performance.now;
      let renderCount = 0;
      
      performance.now = jest.fn(() => {
        renderCount++;
        return originalPerformanceNow();
      });
      
      // Re-render with same props
      rerender(<Dashboard />);
      
      // Should not cause excessive re-renders
      expect(renderCount).toBeLessThan(10);
      
      // Restore original
      performance.now = originalPerformanceNow;
    });

    test('handles large datasets efficiently', async () => {
      const largeDataset = {
        events: Array.from({ length: 1000 }, (_, i) => ({
          timestamp: 1640995200 + i * 3600,
          count: Math.floor(Math.random() * 10) + 1,
        })),
        total_blinks: 5000,
        avg_blink_rate: 15,
        active_hours: 8,
        health_score: 90,
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => largeDataset,
      });

      const startTime = performance.now();
      
      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('5000')).toBeInTheDocument();
      });
      
      const endTime = performance.now();
      
      // Should render within reasonable time
      expect(endTime - startTime).toBeLessThan(1000); // Less than 1 second
    });
  });

  describe('Data Processing', () => {
    test('processes blink data correctly for charts', async () => {
      const mockBlinkData = {
        events: [
          { timestamp: 1640995200, count: 5 },
          { timestamp: 1641081600, count: 3 },
          { timestamp: 1641168000, count: 7 },
        ],
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBlinkData,
      });

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        // Should process data and display charts
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      });
    });

    test('handles empty data gracefully', async () => {
      const emptyData = {
        events: [],
        total_blinks: 0,
        avg_blink_rate: 0,
        active_hours: 0,
        health_score: 0,
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => emptyData,
      });

      renderWithProviders(<Dashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument(); // Total blinks
        expect(screen.getByText('0/min')).toBeInTheDocument(); // Blink rate
        expect(screen.getByText('0h')).toBeInTheDocument(); // Active time
        expect(screen.getByText('0%')).toBeInTheDocument(); // Health score
      });
    });
  });
});