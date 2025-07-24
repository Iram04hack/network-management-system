/**
 * Composant UploadProgress - Barre de progression d'upload
 * Affichage détaillé du progrès avec vitesse et temps restant
 */

import React, { useState, useEffect, useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant UploadProgress
 */
const UploadProgress = ({ 
  progress = 0, 
  fileName = '', 
  fileSize = 0,
  uploadedBytes = 0,
  showDetails = true,
  showSpeed = true,
  showETA = true,
  className = '' 
}) => {
  const [startTime] = useState(Date.now());
  const [lastProgress, setLastProgress] = useState(0);
  const [lastTime, setLastTime] = useState(Date.now());
  const [speeds, setSpeeds] = useState([]);

  // Calculer la vitesse d'upload
  const uploadSpeed = useMemo(() => {
    if (speeds.length === 0) return 0;
    
    // Moyenne des 5 dernières mesures pour lisser
    const recentSpeeds = speeds.slice(-5);
    return recentSpeeds.reduce((sum, speed) => sum + speed, 0) / recentSpeeds.length;
  }, [speeds]);

  // Calculer le temps restant estimé
  const estimatedTimeRemaining = useMemo(() => {
    if (uploadSpeed === 0 || progress >= 100) return 0;
    
    const remainingBytes = fileSize * (100 - progress) / 100;
    return remainingBytes / uploadSpeed; // en secondes
  }, [uploadSpeed, progress, fileSize]);

  // Mettre à jour la vitesse
  useEffect(() => {
    const now = Date.now();
    const timeDiff = (now - lastTime) / 1000; // en secondes
    const progressDiff = progress - lastProgress;
    
    if (timeDiff > 0.5 && progressDiff > 0) { // Mesurer toutes les 500ms minimum
      const bytesDiff = (fileSize * progressDiff / 100);
      const speed = bytesDiff / timeDiff; // bytes par seconde
      
      setSpeeds(prev => [...prev.slice(-9), speed]); // Garder les 10 dernières mesures
      setLastProgress(progress);
      setLastTime(now);
    }
  }, [progress, lastProgress, lastTime, fileSize]);

  // Formatage de la taille
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  // Formatage de la vitesse
  const formatSpeed = (bytesPerSecond) => {
    return formatBytes(bytesPerSecond) + '/s';
  };

  // Formatage du temps
  const formatTime = (seconds) => {
    if (seconds < 60) {
      return Math.round(seconds) + 's';
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  // Déterminer la couleur de la barre selon le progrès
  const getProgressColor = () => {
    if (progress < 30) return '#ff6b6b'; // Rouge
    if (progress < 70) return '#ffa726'; // Orange
    return '#4caf50'; // Vert
  };

  // Calculer les bytes uploadés si pas fournis
  const calculatedUploadedBytes = uploadedBytes || (fileSize * progress / 100);

  return (
    <div className={`upload-progress ${className}`}>
      {/* Barre de progression principale */}
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ 
              width: `${Math.min(progress, 100)}%`,
              backgroundColor: getProgressColor(),
              transition: 'width 0.3s ease'
            }}
          />
        </div>
        <span className="progress-percentage">
          {Math.round(progress)}%
        </span>
      </div>

      {/* Détails de l'upload */}
      {showDetails && (
        <div className="progress-details">
          {/* Nom du fichier */}
          {fileName && (
            <div className="progress-filename">
              <span className="filename-label">📄</span>
              <span className="filename-text" title={fileName}>
                {fileName.length > 30 ? fileName.substring(0, 30) + '...' : fileName}
              </span>
            </div>
          )}

          {/* Informations de taille */}
          {fileSize > 0 && (
            <div className="progress-size">
              <span className="uploaded-size">{formatBytes(calculatedUploadedBytes)}</span>
              <span className="size-separator"> / </span>
              <span className="total-size">{formatBytes(fileSize)}</span>
            </div>
          )}

          {/* Vitesse d'upload */}
          {showSpeed && uploadSpeed > 0 && (
            <div className="progress-speed">
              <span className="speed-icon">⚡</span>
              <span className="speed-value">{formatSpeed(uploadSpeed)}</span>
            </div>
          )}

          {/* Temps restant estimé */}
          {showETA && estimatedTimeRemaining > 0 && progress < 100 && (
            <div className="progress-eta">
              <span className="eta-icon">⏱️</span>
              <span className="eta-value">{formatTime(estimatedTimeRemaining)} restant</span>
            </div>
          )}
        </div>
      )}

      {/* Indicateur d'état */}
      <div className="progress-status">
        {progress === 0 && (
          <span className="status-text preparing">Préparation...</span>
        )}
        {progress > 0 && progress < 100 && (
          <span className="status-text uploading">Upload en cours...</span>
        )}
        {progress >= 100 && (
          <span className="status-text completed">✅ Terminé</span>
        )}
      </div>

      {/* Barre de progression secondaire pour les détails */}
      {showDetails && fileSize > 0 && (
        <div className="progress-segments">
          {/* Segment uploadé */}
          <div 
            className="segment uploaded"
            style={{ width: `${progress}%` }}
            title={`${formatBytes(calculatedUploadedBytes)} uploadés`}
          />
          
          {/* Segment restant */}
          <div 
            className="segment remaining"
            style={{ width: `${100 - progress}%` }}
            title={`${formatBytes(fileSize - calculatedUploadedBytes)} restants`}
          />
        </div>
      )}
    </div>
  );
};

UploadProgress.propTypes = {
  progress: PropTypes.number,
  fileName: PropTypes.string,
  fileSize: PropTypes.number,
  uploadedBytes: PropTypes.number,
  showDetails: PropTypes.bool,
  showSpeed: PropTypes.bool,
  showETA: PropTypes.bool,
  className: PropTypes.string,
};

export default UploadProgress;
