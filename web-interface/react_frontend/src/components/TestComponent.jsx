/**
 * Composant de test minimal pour identifier les erreurs
 */

import React from 'react';

const TestComponent = () => {
  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', margin: '20px' }}>
      <h1>🧪 Test Component</h1>
      <p>Si vous voyez ce message, React fonctionne correctement.</p>
      <p>Timestamp: {new Date().toISOString()}</p>
    </div>
  );
};

export default TestComponent;
