/**
 * Version de test simplifiée de SearchInterface
 * Pour diagnostiquer les problèmes d'affichage
 */

import React, { useState } from 'react';
import { Card, Input, Button, Select, Space, Typography, Divider } from 'antd';
import { SearchOutlined, FilterOutlined, HistoryOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

const SearchInterfaceTest = ({ className = '', ...props }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('all');
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = () => {
    setIsLoading(true);
    console.log('Test search:', searchQuery, searchType);
    setTimeout(() => setIsLoading(false), 1000);
  };

  return (
    <div className={`search-interface-test ${className}`} {...props}>
      <Card title="🔍 Interface de Recherche (Test)" style={{ margin: '16px 0' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {/* Barre de recherche */}
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="Rechercher dans les conversations, documents, messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              prefix={<SearchOutlined />}
              style={{ flex: 1 }}
            />
            <Select
              value={searchType}
              onChange={setSearchType}
              style={{ width: 120 }}
            >
              <Option value="all">Tout</Option>
              <Option value="conversations">Conversations</Option>
              <Option value="documents">Documents</Option>
              <Option value="messages">Messages</Option>
            </Select>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={handleSearch}
              loading={isLoading}
            >
              Rechercher
            </Button>
          </Space.Compact>

          <Divider />

          {/* Filtres */}
          <div>
            <Title level={5}>
              <FilterOutlined /> Filtres
            </Title>
            <Space wrap>
              <Button size="small">Date récente</Button>
              <Button size="small">Par utilisateur</Button>
              <Button size="small">Par tag</Button>
              <Button size="small">Recherche avancée</Button>
            </Space>
          </div>

          <Divider />

          {/* Historique */}
          <div>
            <Title level={5}>
              <HistoryOutlined /> Historique de recherche
            </Title>
            <Space direction="vertical">
              <Text type="secondary">Aucune recherche récente</Text>
            </Space>
          </div>

          <Divider />

          {/* Résultats */}
          <div>
            <Title level={5}>Résultats</Title>
            {isLoading ? (
              <Text>Recherche en cours...</Text>
            ) : (
              <Text type="secondary">
                Effectuez une recherche pour voir les résultats
              </Text>
            )}
          </div>

          {/* Statistiques */}
          <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
            <Text strong>📊 Statistiques de test :</Text>
            <br />
            <Text type="secondary">
              • Composant SearchInterface chargé avec succès ✅
              <br />
              • Hooks Redux contournés pour test ⚠️
              <br />
              • Interface utilisateur fonctionnelle ✅
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default SearchInterfaceTest;
