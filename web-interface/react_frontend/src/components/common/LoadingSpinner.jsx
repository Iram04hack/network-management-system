/**
 * LoadingSpinner - Composant de chargement réutilisable
 * Différentes tailles et styles
 */

import React, { memo } from 'react';
import PropTypes from 'prop-types';
import './LoadingSpinner.css';

const LoadingSpinner = ({
  size = 'medium',
  message = '',
  overlay = false,
  className = '',
}) => {
  const spinnerClass = `loading-spinner ${size} ${overlay ? 'overlay' : ''} ${className}`;

  return (
    <div className={spinnerClass}>
      <div className="spinner-container">
        <div className="spinner">
          <div className="spinner-circle"></div>
          <div className="spinner-circle"></div>
          <div className="spinner-circle"></div>
        </div>
        {message && <div className="spinner-message">{message}</div>}
      </div>
    </div>
  );
};

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  message: PropTypes.string,
  overlay: PropTypes.bool,
  className: PropTypes.string,
};

export default memo(LoadingSpinner);
