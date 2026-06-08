import React from 'react';

function CostTelemetry({ costData }) {
  if (!costData) return null;

  const { model, totalInputTokens, totalOutputTokens, accumulatedCost } = costData;

  const formatCost = (cost) => {
    if (cost == null) return '$0.0000';
    if (cost < 0.0001) return '$0.0000';
    return `$${cost.toFixed(4)}`;
  };

  return (
    <div className="cost-badge">
      <div className="cost-item">
        <span className="cost-label">Model</span>
        <span className="cost-value" style={{ fontSize: '0.7rem' }}>
          {model?.split('-').slice(0, 3).join('-') || '—'}
        </span>
      </div>

      <div className="divider" />

      <div className="cost-item">
        <span className="cost-label">Tokens In</span>
        <span className="cost-value">{totalInputTokens?.toLocaleString() || '0'}</span>
      </div>

      <div className="divider" />

      <div className="cost-item">
        <span className="cost-label">Tokens Out</span>
        <span className="cost-value">{totalOutputTokens?.toLocaleString() || '0'}</span>
      </div>

      <div className="divider" />

      <div className="cost-item">
        <span className="cost-label">Total Cost</span>
        <span className="cost-value green">{formatCost(accumulatedCost)}</span>
      </div>
    </div>
  );
}

export default CostTelemetry;
