/**
 * ErrorBoundary - Composant pour capturer les erreurs React
 * Affichage d'erreur gracieux
 */

import React, { Component } from 'react';
import PropTypes from 'prop-types';
import './ErrorBoundary.css';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // Met à jour le state pour afficher l'UI d'erreur
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log l'erreur pour le debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Ici on pourrait envoyer l'erreur à un service de monitoring
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
    
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  render() {
    if (this.state.hasError) {
      // UI d'erreur personnalisée
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.state.errorInfo, this.handleRetry);
      }

      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <div className="error-icon">⚠️</div>
            <h2 className="error-title">
              {this.props.title || 'Une erreur est survenue'}
            </h2>
            <p className="error-message">
              {this.props.message || 'Quelque chose s\'est mal passé. Veuillez réessayer.'}
            </p>
            
            {this.props.showDetails && this.state.error && (
              <details className="error-details">
                <summary>Détails de l'erreur</summary>
                <pre className="error-stack">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack || ''}
                </pre>
              </details>
            )}
            
            <div className="error-actions">
              <button 
                className="retry-button primary"
                onClick={this.handleRetry}
              >
                Réessayer
              </button>
              
              {this.props.onReload && (
                <button 
                  className="reload-button"
                  onClick={this.props.onReload}
                >
                  Recharger la page
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.string,
  message: PropTypes.string,
  showDetails: PropTypes.bool,
  fallback: PropTypes.func,
  onError: PropTypes.func,
  onRetry: PropTypes.func,
  onReload: PropTypes.func,
};

ErrorBoundary.defaultProps = {
  showDetails: import.meta.env.DEV,
};

export default ErrorBoundary;
