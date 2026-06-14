import { useEffect, useRef } from 'react';
import { createViewerApp as origCreateViewerApp } from '@document-kits/viewer';
import type { PDFViewerApplication } from '@document-kits/viewer';
import { createBlockAnnotationPlugin } from '../plugins/blockAnnotations';
import type { BlockStyleConfig } from '../plugins/blockAnnotations';

const CSS_BASE = '/static/document-viewer/web';
const CSS_URL = `${CSS_BASE}/viewer.css`;

interface PdfViewerProps {
  src: string;
  runId?: string | null;
  blockStyleConfig?: BlockStyleConfig;
  sharedPlugins?: any[];
  scrollFraction?: number;
  onScrollChange?: (fraction: number) => void;
}

export function PdfViewer({ src, runId, blockStyleConfig, sharedPlugins, scrollFraction, onScrollChange }: PdfViewerProps) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<PDFViewerApplication | null>(null);
  const shadowRef = useRef<ShadowRoot | null>(null);
  const scrollRef = useRef<HTMLElement | null>(null);
  const onScrollChangeRef = useRef(onScrollChange);
  onScrollChangeRef.current = onScrollChange;
  const syncingRef = useRef(false);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;

    if (appRef.current) {
      appRef.current.close();
      appRef.current = null;
    }

    let shadow = shadowRef.current;
    if (!shadow) {
      shadow = wrapper.attachShadow({ mode: 'open' });
      shadowRef.current = shadow;
    }

    while (shadow.firstChild) {
      shadow.removeChild(shadow.firstChild);
    }

    const container = document.createElement('div');
    container.style.height = '100%';

    let cancelled = false;

    fetch(CSS_URL)
      .then(r => r.text())
      .then(css => {
        if (cancelled) return;
        const rewritten = css
          .replace(/^:root\b/gm, ':host')
          .replace(/^html,\s*body\s*\{/gm, ':host {')
          .replace(/^body\s*\{/gm, ':host {')
          .replace(/url\(["']images\//g, `url("${CSS_BASE}/images/`);

        const baseStyle = document.createElement('style');
        const overrides = [
          '.annotationLayer .linkAnnotation{display:none!important;outline:none!important}',
          '.annotationLayer .linkAnnotation>a{display:none!important;outline:none!important;border:none!important}',
          '.toolbar{z-index:1!important}',
          '.toolbarContainer{z-index:1!important}',
          '.findbar{z-index:1!important}',
          '.secondaryToolbar{z-index:1!important}',
          '.editorParamsToolbar{z-index:1!important}',
          '.sidebarResizer{z-index:1!important}',
        ].join('');
        baseStyle.textContent = rewritten + overrides;
        shadow!.appendChild(baseStyle);
        shadow!.appendChild(container);

        let plugins: any[];
        if (sharedPlugins) {
          if (runId) {
            const p = createBlockAnnotationPlugin(runId, blockStyleConfig);
            if (!sharedPlugins.includes(p)) sharedPlugins.push(p);
          }
          plugins = [...sharedPlugins];
        } else {
          plugins = runId ? [createBlockAnnotationPlugin(runId, blockStyleConfig)] : [];
        }

        if (runId) {
          container.setAttribute('data-docalchemy-run', runId);
        }

        appRef.current = origCreateViewerApp({
          parent: container,
          src,
          resourcePath: '/static/document-viewer',
          disableCORSCheck: true,
          disableAutoSetTitle: true,
          plugins,
        });

        let retries = 20;
        const trySetup = () => {
          if (cancelled) return;
          const sc = shadow!.querySelector('[data-dom-id="viewerContainer"]') as HTMLElement | null;
          if (sc) {
            scrollRef.current = sc;
            sc.addEventListener('scroll', () => {
              if (syncingRef.current) return;
              const max = sc.scrollHeight - sc.clientHeight;
              if (max <= 0) return;
              onScrollChangeRef.current?.(sc.scrollTop / max);
            }, { passive: true });
            return;
          }
          if (--retries > 0) {
            setTimeout(trySetup, 200);
          }
        };
        setTimeout(trySetup, 500);
      })
      .catch(console.error);

    return () => {
      cancelled = true;
      appRef.current?.close();
      appRef.current = null;
      scrollRef.current = null;
    };
  }, [src, runId, blockStyleConfig]);

  const prevScrollRef = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (scrollFraction === undefined || scrollFraction === prevScrollRef.current) return;
    prevScrollRef.current = scrollFraction;
    const sc = scrollRef.current;
    if (!sc) return;
    const max = sc.scrollHeight - sc.clientHeight;
    if (max <= 0) return;
    syncingRef.current = true;
    sc.scrollTop = scrollFraction * max;
    requestAnimationFrame(() => { syncingRef.current = false; });
  }, [scrollFraction]);

  return <div ref={wrapperRef} className="w-full h-full" style={{ position: 'relative', zIndex: 0 }} />;
}
