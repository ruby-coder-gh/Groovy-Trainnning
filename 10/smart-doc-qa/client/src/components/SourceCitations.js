import React from 'react';

function SourceCitations({ citations }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="citations-card">
      <h3>📚 Source Citations</h3>
      {citations.map((citation, i) => (
        <div key={i} className="citation-item">
          <div className="citation-page">📄 Page {citation.page}</div>
          <div className="citation-excerpt">
            &ldquo;{citation.excerpt}&rdquo;
          </div>
        </div>
      ))}
    </div>
  );
}

export default SourceCitations;
