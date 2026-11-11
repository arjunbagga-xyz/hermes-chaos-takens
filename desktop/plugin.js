import { PANES_AREA, STATUSBAR_AREAS, TRANSCRIPT_DIRECTIVE_AREA, host } from '@hermes/plugin-sdk';
import { jsx } from 'react/jsx-runtime';

function TakensDirectiveCard({ attrs }) {
  const data = attrs || {};
  const lam1 = data.lambda_1;
  const horizon = data.horizon;
  const regime = data.regime;
  const pts = Array.isArray(data.pts) ? data.pts : [];

  const hasData = typeof lam1 === 'number' && pts.length > 0;

  if (!hasData) {
    return jsx('div', {
      style: { color: 'var(--ui-text-secondary)', fontSize: '11px', fontFamily: 'var(--ui-font-mono)' },
      children: 'chaos-takens · idle · no series loaded'
    });
  }

  return jsx('div', {
    style: { color: 'var(--ui-text-primary)', fontSize: '11px', fontFamily: 'var(--ui-font-mono)' },
    children: `chaos-takens · λ₁=${lam1.toFixed(4)} (${regime.replace('_', ' ')}) · T_max=${horizon.toFixed(2)} steps · ${pts.length} live manifold points`
  });
}

export default {
  id: 'chaos-takens',
  name: 'Chaos Takens Manifold Manifold',
  register(ctx) {
    ctx.register({
      id: 'directive',
      area: TRANSCRIPT_DIRECTIVE_AREA,
      data: {
        name: 'chaos-takens',
        render: ({ attrs, sessionId }) => jsx(TakensDirectiveCard, { attrs, sessionId })
      }
    });
    ctx.register({
      id: 'chip',
      area: STATUSBAR_AREAS.right,
      order: 123,
      render: () => jsx('button', {
        type: 'button',
        className: 'px-2 text-[0.6875rem] text-(--ui-text-secondary)',
        onClick: () => host.notify({ kind: 'info', message: 'Chaos Takens: run a reconstruction to populate λ₁, horizon, and phase portrait' }),
        children: '🌀 chaos-takens · λ₁: --'
      })
    });
  }
};
