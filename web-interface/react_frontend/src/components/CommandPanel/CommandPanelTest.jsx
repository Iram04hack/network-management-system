/**
 * Version de test simplifiée de CommandPanel
 * Pour diagnostiquer les problèmes d'affichage
 */

import React, { useState } from 'react';
import { Card, Input, Button, List, Typography, Space, Tag, Divider } from 'antd';
import { 
  TerminalOutlined, 
  PlayCircleOutlined, 
  HistoryOutlined,
  InfoCircleOutlined 
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const CommandPanelTest = ({ className = '', ...props }) => {
  const [command, setCommand] = useState('');
  const [output, setOutput] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [commandHistory, setCommandHistory] = useState([]);

  // Commandes disponibles pour test
  const availableCommands = [
    { name: 'scan', description: 'Scanner le réseau', category: 'network', syntax: 'scan <target> [port-range]' },
    { name: 'ping', description: 'Ping un hôte', category: 'network', syntax: 'ping <host>' },
    { name: 'traceroute', description: 'Tracer la route vers un hôte', category: 'network', syntax: 'traceroute <destination>' },
    { name: 'sysinfo', description: 'Informations système', category: 'system', syntax: 'sysinfo' },
    { name: 'diskspace', description: 'Espace disque', category: 'system', syntax: 'diskspace' },
    { name: 'processes', description: 'Liste des processus', category: 'system', syntax: 'processes' },
    { name: 'help', description: 'Afficher l\'aide', category: 'utility', syntax: 'help [command]' },
    { name: 'clear', description: 'Effacer le terminal', category: 'utility', syntax: 'clear' },
    { name: 'history', description: 'Historique des commandes', category: 'utility', syntax: 'history' },
  ];

  const executeCommand = () => {
    if (!command.trim()) return;

    setIsExecuting(true);
    const newHistory = [...commandHistory, command];
    setCommandHistory(newHistory);

    // Simulation d'exécution
    setTimeout(() => {
      let result = '';
      
      if (command === 'help') {
        result = 'Commandes disponibles:\n' + 
                availableCommands.map(cmd => `${cmd.name} - ${cmd.description}`).join('\n');
      } else if (command === 'clear') {
        setOutput('');
        setIsExecuting(false);
        setCommand('');
        return;
      } else if (command === 'history') {
        result = 'Historique des commandes:\n' + 
                newHistory.map((cmd, i) => `${i + 1}. ${cmd}`).join('\n');
      } else if (command.startsWith('ping')) {
        result = `PING ${command.split(' ')[1] || 'localhost'}\n64 bytes from localhost: icmp_seq=1 ttl=64 time=0.123 ms\n--- ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss`;
      } else {
        result = `Commande exécutée: ${command}\nRésultat simulé pour test`;
      }

      setOutput(prev => prev + `$ ${command}\n${result}\n\n`);
      setCommand('');
      setIsExecuting(false);
    }, 1000);
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'network': return 'blue';
      case 'system': return 'green';
      case 'utility': return 'orange';
      default: return 'default';
    }
  };

  return (
    <div className={`command-panel-test ${className}`} {...props}>
      <Card title="💻 Panneau de Commandes (Test)" style={{ margin: '16px 0' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {/* Terminal */}
          <div>
            <Title level={5}>
              <TerminalOutlined /> Terminal
            </Title>
            <TextArea
              value={output}
              placeholder="Sortie des commandes..."
              rows={8}
              readOnly
              style={{ 
                fontFamily: 'monospace', 
                backgroundColor: '#000', 
                color: '#00ff00',
                border: '1px solid #333'
              }}
            />
          </div>

          {/* Saisie de commande */}
          <Space.Compact style={{ width: '100%' }}>
            <Input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onPressEnter={executeCommand}
              placeholder="Tapez votre commande..."
              prefix={<Text style={{ color: '#666' }}>$</Text>}
              style={{ fontFamily: 'monospace' }}
            />
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={executeCommand}
              loading={isExecuting}
            >
              Exécuter
            </Button>
          </Space.Compact>

          <Divider />

          {/* Commandes disponibles */}
          <div>
            <Title level={5}>
              <InfoCircleOutlined /> Commandes disponibles
            </Title>
            <List
              size="small"
              dataSource={availableCommands}
              renderItem={(cmd) => (
                <List.Item>
                  <Space>
                    <Tag color={getCategoryColor(cmd.category)}>{cmd.category}</Tag>
                    <Text strong>{cmd.name}</Text>
                    <Text type="secondary">{cmd.description}</Text>
                    <Text code>{cmd.syntax}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </div>

          <Divider />

          {/* Historique */}
          <div>
            <Title level={5}>
              <HistoryOutlined /> Historique
            </Title>
            {commandHistory.length > 0 ? (
              <Space wrap>
                {commandHistory.slice(-5).map((cmd, i) => (
                  <Tag 
                    key={i} 
                    onClick={() => setCommand(cmd)}
                    style={{ cursor: 'pointer' }}
                  >
                    {cmd}
                  </Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">Aucune commande exécutée</Text>
            )}
          </div>

          {/* Statistiques */}
          <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
            <Text strong>📊 Statistiques de test :</Text>
            <br />
            <Text type="secondary">
              • Composant CommandPanel chargé avec succès ✅
              <br />
              • Hooks Redux contournés pour test ⚠️
              <br />
              • Terminal simulé fonctionnel ✅
              <br />
              • {availableCommands.length} commandes disponibles
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default CommandPanelTest;
