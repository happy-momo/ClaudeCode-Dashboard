import type { ReactNode, ChangeEvent } from 'react';

interface PageLayoutProps {
  title: string;
  description: string;
  children: ReactNode;
  className?: string;
}

/**
 * Unified page layout component to ensure consistent height and structure
 * across all management interfaces (History, Skills, MCPs, Plugins, Unified View)
 *
 * Prevents:
 * - Container overlaps
 * - Content overflow
 * - Inconsistent page heights during navigation
 */
export function PageLayout({ title, description, children, className = '' }: PageLayoutProps) {
  return (
    <div className={`space-y-6 animate-in fade-in duration-500 ${className}`}>
      {/* Page Header - Fixed height section */}
      <div className="shrink-0">
        <h2 className="text-3xl font-serif text-anthro-text-heading tracking-tight">
          {title}
        </h2>
        <p className="text-anthro-text-body text-sm mt-1 font-medium">
          {description}
        </p>
      </div>

      {/* Page Content - Handles its own scrolling */}
      <div className="min-h-0">
        {children}
      </div>
    </div>
  );
}

interface PageToolbarProps {
  children: ReactNode;
  className?: string;
}

/**
 * Toolbar component for search bars and action buttons
 * Ensures consistent spacing and layout
 */
export function PageToolbar({ children, className = '' }: PageToolbarProps) {
  return (
    <div className={`mb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4 shrink-0 ${className}`}>
      {children}
    </div>
  );
}

interface PageContentProps {
  children: ReactNode;
  className?: string;
}

/**
 * Content area with proper overflow handling
 * Use this for tables, card lists, or scrollable content
 */
export function PageContent({ children, className = '' }: PageContentProps) {
  return (
    <div className={`min-h-0 ${className}`}>
      {children}
    </div>
  );
}

interface ScrollableContentProps {
  children: ReactNode;
  className?: string;
  /** Max height for the scrollable area */
  maxHeight?: string;
}

/**
 * Scrollable content container with fixed max height
 * Ensures content doesn't overflow the viewport
 *
 * @param maxHeight - CSS height value (e.g., "500px", "60vh")
 */
export function ScrollableContent({ children, className = '', maxHeight = '60vh' }: ScrollableContentProps) {
  return (
    <div
      className={`overflow-y-auto ${className}`}
      style={{ maxHeight }}
    >
      {children}
    </div>
  );
}

interface PagePaginationProps {
  children: ReactNode;
  className?: string;
}

/**
 * Pagination component wrapper
 * Ensures consistent positioning and spacing
 */
export function PagePagination({ children, className = '' }: PagePaginationProps) {
  return (
    <div className={`mt-4 flex justify-between items-center shrink-0 ${className}`}>
      {children}
    </div>
  );
}

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  onSearchChange?: (value: string) => void;
}

/**
 * Standardized search bar component
 * Automatically resets pagination when search changes
 */
export function SearchBar({
  value,
  onChange,
  placeholder = "Search...",
  className = '',
  onSearchChange
}: SearchBarProps) {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    onSearchChange?.(newValue);
  };

  return (
    <div className={`relative flex-1 max-w-md ${className}`}>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={handleChange}
        className="w-full pl-10 pr-4 py-2.5 border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-body text-sm placeholder:text-anthro-text-muted focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent transition-colors"
      />
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-anthro-text-muted"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
  );
}

interface ResultCountProps {
  count: number;
  singular?: string;
  plural?: string;
  className?: string;
}

/**
 * Display result count with proper pluralization
 */
export function ResultCount({
  count,
  singular = 'result',
  plural = 'results',
  className = ''
}: ResultCountProps) {
  return (
    <p className={`text-sm text-anthro-text-muted ${className}`}>
      Found {count} {count === 1 ? singular : plural}
    </p>
  );
}
