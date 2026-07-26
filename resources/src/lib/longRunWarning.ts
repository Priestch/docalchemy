import { ProviderDefinition } from '../types';

/**
 * If the selected provider has a recommended page limit and the document
 * exceeds it, prompt the user to confirm before triggering what could be a
 * very long-running analysis. Returns true when the run may proceed.
 *
 * `max_pages === null` means the provider has no limit — always proceeds.
 */
export function confirmLongRun(
  provider: ProviderDefinition | undefined,
  pageCount: number | undefined,
): boolean {
  if (!provider || !provider.max_pages) return true;
  if (pageCount === undefined || pageCount <= provider.max_pages) return true;

  return window.confirm(
    `This document has ${pageCount} pages.\n` +
      `${provider.display_name} is recommended for documents up to ` +
      `${provider.max_pages} pages and may take a long time to process ` +
      `(for slow providers this can be minutes per page).\n\n` +
      `Start the analysis anyway?`,
  );
}
