/**
 * Fetches every page of a skip/limit list endpoint.
 *
 * Backend list endpoints cap `limit` at 1000 and return a plain array,
 * so keep requesting pages until a short batch signals the end.
 */
export async function fetchAllPages<T>(
  fetchPage: (skip: number, limit: number) => Promise<T[]>,
  pageSize = 1000,
): Promise<T[]> {
  const all: T[] = [];
  for (let skip = 0; ; skip += pageSize) {
    const batch = await fetchPage(skip, pageSize);
    all.push(...batch);
    if (batch.length < pageSize) return all;
  }
}
