import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const useKeyboardShortcuts = (onOpenSearch) => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignorer si l'utilisateur tape dans un input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        // Exception pour Ctrl+K qui doit toujours fonctionner
        if (!(e.ctrlKey || e.metaKey) || e.key !== 'k') {
          return;
        }
      }

      const isCtrlOrCmd = e.ctrlKey || e.metaKey;

      // Raccourcis avec Ctrl/Cmd
      if (isCtrlOrCmd) {
        switch (e.key.toLowerCase()) {
          case 'k':
            e.preventDefault();
            onOpenSearch();
            break;
          case 'd':
            e.preventDefault();
            navigate('/dashboard');
            break;
          case 'm':
            e.preventDefault();
            navigate('/monitoring');
            break;
          case 'e':
            e.preventDefault();
            navigate('/equipments');
            break;
          case 's':
            e.preventDefault();
            navigate('/security');
            break;
          case 'q':
            e.preventDefault();
            navigate('/qos');
            break;
          case 'g':
            e.preventDefault();
            navigate('/gns3');
            break;
          case 'r':
            e.preventDefault();
            navigate('/reports');
            break;
        }
      }

      // Raccourcis avec Alt
      if (e.altKey) {
        switch (e.key) {
          case '1':
            e.preventDefault();
            navigate('/dashboard');
            break;
          case '2':
            e.preventDefault();
            navigate('/monitoring');
            break;
          case '3':
            e.preventDefault();
            navigate('/equipments');
            break;
          case '4':
            e.preventDefault();
            navigate('/security');
            break;
          case '5':
            e.preventDefault();
            navigate('/qos');
            break;
          case '6':
            e.preventDefault();
            navigate('/gns3');
            break;
          case '7':
            e.preventDefault();
            navigate('/reports');
            break;
        }
      }

      // Raccourci simple
      if (!isCtrlOrCmd && !e.altKey && !e.shiftKey) {
        switch (e.key) {
          case '/':
            e.preventDefault();
            onOpenSearch();
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [navigate, onOpenSearch]);

  // Retourner la liste des raccourcis pour l'aide
  return {
    shortcuts: [
      { key: 'Ctrl+K', description: 'Ouvrir la recherche' },
      { key: '/', description: 'Ouvrir la recherche' },
      { key: 'Ctrl+D', description: 'Aller au dashboard' },
      { key: 'Ctrl+M', description: 'Aller au monitoring' },
      { key: 'Ctrl+E', description: 'Aller aux équipements' },
      { key: 'Ctrl+S', description: 'Aller à la sécurité' },
      { key: 'Alt+1-7', description: 'Navigation rapide par numéro' },
    ]
  };
};