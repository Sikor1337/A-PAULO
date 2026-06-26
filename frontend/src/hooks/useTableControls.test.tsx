import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useTableControls } from './useTableControls';

interface Row {
  name: string;
  city: string;
  visits: number;
  active: boolean;
}

const rows: Row[] = [
  { name: 'Celina', city: 'Krakow', visits: 3, active: true },
  { name: 'Adam', city: 'Warsaw', visits: 1, active: false },
  { name: 'Basia', city: 'Krakow', visits: 2, active: true },
];

const names = (items: Row[]) => items.map((row) => row.name);

describe('useTableControls', () => {
  it('sorts rows by the initial column', () => {
    const { result } = renderHook(() =>
      useTableControls(rows, {
        searchFields: ['name', 'city'],
        initialSort: 'name',
      }),
    );

    expect(names(result.current.rows)).toEqual(['Adam', 'Basia', 'Celina']);
    expect(result.current.sortIcon('name')).toBe(' \u2191');
  });

  it('filters rows by free-text search and custom predicate', () => {
    const { result } = renderHook(() =>
      useTableControls(rows, {
        searchFields: ['name', 'city'],
        initialSort: 'name',
        filterPredicate: (row) => row.active,
      }),
    );

    act(() => result.current.setSearch('krak'));

    expect(names(result.current.rows)).toEqual(['Basia', 'Celina']);
  });

  it('toggles sort direction and supports custom comparators', () => {
    const { result } = renderHook(() =>
      useTableControls(rows, {
        searchFields: ['name', 'city'],
        initialSort: 'name',
        comparators: {
          visits: (a, b) => a.visits - b.visits,
        },
      }),
    );

    act(() => result.current.toggleSort('visits'));
    expect(names(result.current.rows)).toEqual(['Adam', 'Basia', 'Celina']);

    act(() => result.current.toggleSort('visits'));
    expect(names(result.current.rows)).toEqual(['Celina', 'Basia', 'Adam']);
    expect(result.current.sortIcon('visits')).toBe(' \u2193');
  });
});
