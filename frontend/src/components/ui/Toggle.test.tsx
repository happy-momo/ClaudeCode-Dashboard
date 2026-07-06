import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Toggle } from '@/components/ui/Toggle';

describe('Toggle', () => {
  it('renders as a switch role', () => {
    render(<Toggle checked={false} onChange={() => {}} />);
    expect(screen.getByRole('switch')).toBeInTheDocument();
  });

  it('shows checked state', () => {
    render(<Toggle checked={true} onChange={() => {}} />);
    const toggle = screen.getByRole('switch');
    expect(toggle.getAttribute('aria-checked')).toBe('true');
  });

  it('shows unchecked state', () => {
    render(<Toggle checked={false} onChange={() => {}} />);
    const toggle = screen.getByRole('switch');
    expect(toggle.getAttribute('aria-checked')).toBe('false');
  });

  it('calls onChange when clicked', () => {
    let newValue = false;
    render(<Toggle checked={false} onChange={(v) => { newValue = v; }} />);
    fireEvent.click(screen.getByRole('switch'));
    expect(newValue).toBe(true);
  });
});
