import { describe, it, expect } from 'vitest';
import { ApiError } from '@/api/client';

describe('ApiError', () => {
  it('stores status code and message', () => {
    const error = new ApiError(404, 'Not found');
    expect(error.status).toBe(404);
    expect(error.message).toBe('Not found');
    expect(error.name).toBe('ApiError');
  });

  it('stores details', () => {
    const details = { field: 'name', issue: 'required' };
    const error = new ApiError(422, 'Validation error', details);
    expect(error.details).toEqual(details);
  });
});
