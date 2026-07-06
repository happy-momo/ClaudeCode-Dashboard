import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card } from '@/components/ui/Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('has card container with surface styling', () => {
    const { container } = render(<Card>Test</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toBeTruthy();
    expect(card.className).toContain('bg-anthro-surface');
    expect(card.className).toContain('rounded-2xl');
  });

  it('applies default medium padding', () => {
    const { container } = render(<Card>Test</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('p-6');
  });

  it('applies large padding', () => {
    const { container } = render(<Card padding="lg">Test</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('p-8');
  });

  it('applies small padding', () => {
    const { container } = render(<Card padding="sm">Test</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('p-4');
  });
});
