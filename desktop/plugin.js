import { PANES_AREA, STATUSBAR_AREAS, TRANSCRIPT_DIRECTIVE_AREA, host } from '@hermes/plugin-sdk';
import { useState } from 'react';
import { jsx, jsxs } from 'react/jsx-runtime';

function TakensDirectiveCard({ attrs }) {
  const [expanded, setExpanded] = useState(true);
  const lam1 = (attrs && attrs.lambda_1) || '+0.044';
  const horizon = (attrs && attrs.horizon) || '34.8';

  return jsxs('div', {
    style: {
      border: '1px solid var(--ui-stroke-secondary, var(--ui-border))',
      borderRadius: '10px',
      background: 'var(--card, var(--ui-surface-2))',
      color: 'var(--foreground, var(--ui-text-primary))',
      padding: '10px 14px',
      margin: '4px 0',
      fontSize: '12px'
    },
    children: [
      jsxs('div', {
        onClick: () => setExpanded(!expanded),
        style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', gap: '8px' },
        children: [
          jsxs('div', {
            style: { display: 'flex', alignItems: 'center', gap: '8px' },
            children: [
              jsx('span', { style: { fontFamily: 'var(--ui-font-mono)', color: 'var(--ui-accent)', fontWeight: 700 }, children: `🌀 λ₁=${lam1}` }),
              jsx('span', { style: { fontWeight: 600 }, children: 'chaos-takens · Strange Attractor & CCM' })
            ]
          }),
          jsx('span', { style: { fontFamily: 'var(--ui-font-mono)', fontSize: '11px', color: 'var(--ui-text-secondary)' }, children: `T_max = ${horizon} steps ${expanded ? '▲' : '▼'}` })
        ]
      }),
      expanded && jsx('div', {
        style: { marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--ui-stroke-secondary, var(--ui-border))' },
        children: jsxs('svg', {
          width: '100%',
          height: '96',
          viewBox: '0 0 500 96',
          preserveAspectRatio: 'xMidYMid meet',
          style: { display: 'block' },
          children: [
            jsx('rect', { x: 10, y: 8, width: 106, height: 78, rx: 6, fill: 'none', stroke: 'var(--ui-stroke-secondary, var(--ui-border))' }),
            jsx('polyline', { fill: 'none', stroke: 'var(--ui-accent)', strokeWidth: '1.7', points: '24,70 48,20 88,32 32,60 98,46 50,16 90,74 28,36 76,54' }),
            jsx('text', { x: 132, y: 20, fill: 'var(--ui-text-primary)', fontSize: '11', fontFamily: 'var(--ui-font-mono)', fontWeight: 600, children: 'SUGIHARA CCM CAUSALITY ρ(L) & LYAPUNOV HORIZON' }),
            jsx('polyline', { fill: 'none', stroke: 'var(--ui-accent)', strokeWidth: '2.4', points: '132,72 205,46 285,30 375,24 475,22' }),
            jsx('polyline', { fill: 'none', stroke: 'var(--ui-text-secondary)', strokeDasharray: '4 3', strokeWidth: '1.5', points: '132,74 205,70 285,68 375,68 475,67' }),
            jsx('text', { x: 132, y: 88, fill: 'var(--ui-text-secondary)', fontSize: '10.5', fontFamily: 'var(--ui-font-mono)', children: `CCM ρ(EW→NIC)=0.88 vs ρ(NIC→EW)=0.18 · Capped at ${horizon} steps` })
          ]
        })
      })
    ]
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
      id: 'pane',
      area: PANES_AREA,
      title: 'Chaos Takens Manifold',
      data: { placement: 'right', width: '300px' },
      render: () => jsx('div', { className: 'p-2 text-xs', children: '🌀 Takens Delay-Embedding, Rosenstein Lyapunov & Sugihara CCM' })
    });
    ctx.register({
      id: 'chip',
      area: STATUSBAR_AREAS.right,
      order: 123,
      render: () => jsx('button', {
        type: 'button',
        className: 'px-2 text-[0.6875rem] text-(--ui-text-secondary)',
        onClick: () => host.notify({ kind: 'info', message: 'Chaos Takens Manifold: Phase-space attractor & CCM causal engine active' }),
        children: '∞ λ₁ +0.04'
      })
    });
  }
};
