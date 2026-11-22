jest.mock('axios', () => {
  const client = {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    put: jest.fn(),
    request: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };

  return {
    __esModule: true,
    default: {
      ...client,
      create: jest.fn(() => client),
    },
  };
});

import App from './App';

test('exports the application shell component', () => {
  expect(typeof App).toBe('function');
});
