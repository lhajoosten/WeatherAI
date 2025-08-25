import { http, HttpResponse } from 'msw';

// Mock data for different endpoints
const mockLocations = [
  { id: '1', name: 'Amsterdam', country: 'Netherlands', lat: 52.3676, lon: 4.9041 },
  { id: '2', name: 'Rotterdam', country: 'Netherlands', lat: 51.9244, lon: 4.4777 },
  { id: '3', name: 'Utrecht', country: 'Netherlands', lat: 52.0907, lon: 5.1214 },
];

const mockMeta = {
  version: '1.0.0',
  features: {
    rag: true,
    analytics: false,
  },
  limits: {
    maxQueryLength: 1000,
    rateLimit: 100,
  },
};

export const handlers = [
  // Health check endpoint
  http.get('/api/v1/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'healthy',
        redis: 'healthy',
        openai: 'healthy',
      },
    });
  }),

  // Meta endpoint
  http.get('/api/v1/meta', () => {
    return HttpResponse.json(mockMeta);
  }),

  // Locations search endpoint
  http.get('/api/v1/locations/search', ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('q') || '';
    
    if (!query) {
      return HttpResponse.json({ locations: [] });
    }

    const filteredLocations = mockLocations.filter(location =>
      location.name.toLowerCase().includes(query.toLowerCase()) ||
      location.country.toLowerCase().includes(query.toLowerCase())
    );

    return HttpResponse.json({ locations: filteredLocations });
  }),

  // RAG ask endpoint
  http.post('/api/v1/rag/ask', async ({ request }) => {
    const body = await request.json() as { query: string };
    
    if (!body.query) {
      return new HttpResponse(
        JSON.stringify({ message: 'Query is required' }),
        { status: 400 }
      );
    }

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    return HttpResponse.json({
      answer: `This is a mock answer to your question: "${body.query}". The RAG system would provide relevant information based on your query.`,
      sources: [
        {
          id: 'doc-1',
          title: 'Weather Documentation',
          excerpt: 'Relevant excerpt from weather documentation...',
          relevance: 0.95,
        },
        {
          id: 'doc-2',
          title: 'Climate Data',
          excerpt: 'Climate data showing historical patterns...',
          relevance: 0.87,
        },
      ],
      confidence: 0.91,
    });
  }),

  // Error simulation endpoints for testing
  http.get('/api/v1/test/error/500', () => {
    return new HttpResponse(
      JSON.stringify({ message: 'Internal server error' }),
      { status: 500 }
    );
  }),

  http.get('/api/v1/test/error/timeout', () => {
    // Simulate timeout by never responding
    return new Promise(() => {});
  }),

  http.get('/api/v1/test/error/network', () => {
    return HttpResponse.error();
  }),
];