import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('applies primary variant styles by default', () => {
    render(<Button>Primary</Button>);
    const button = screen.getByText('Primary');
    expect(button.className).toContain('bg-anthro-accent');
  });

  it('applies secondary variant styles', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByText('Secondary');
    expect(button.className).toContain('border');
  });

  it('applies danger variant styles', () => {
    render(<Button variant="danger">Danger</Button>);
    const button = screen.getByText('Danger');
    expect(button.className).toContain('text-[#B55A30]');
  });

  it('applies size styles', () => {
    render(<Button size="sm">Small</Button>);
    const button = screen.getByText('Small');
    expect(button.className).toContain('text-xs');
  });

  it('handles onClick', async () => {
    let clicked = false;
    render(<Button onClick={() => { clicked = true; }}>Click</Button>);
    const button = screen.getByText('Click');
    button.click();
    expect(clicked).toBe(true);
  });

  it('supports type attribute', () => {
    render(<Button type="submit">Submit</Button>);
    const button = screen.getByText('Submit');
    expect(button.getAttribute('type')).toBe('submit');
  });
});
