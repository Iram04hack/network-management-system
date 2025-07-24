import React, { useState, useEffect, useRef } from 'react';
import { Button, Tabs, Badge, Tooltip, Card } from 'antd';
import {
  CloseOutlined,
  RobotOutlined,
  MessageOutlined,
  FileTextOutlined,
  UploadOutlined,
  SearchOutlined,
  CodeOutlined
} from '@ant-design/icons';
import ErrorBoundary from './common/ErrorBoundary';

// Import progressif des composants avec gestion d'erreurs
let ConversationList, MessageThread, DocumentUploader, SearchInterface, CommandPanel;

try {
  ConversationList = require('./ConversationList/ConversationList').default;
} catch (error) {
  console.error('Erreur import ConversationList:', error);
  ConversationList = () => <div>Erreur: ConversationList</div>;
}

try {
  MessageThread = require('./MessageThread/MessageThread').default;
} catch (error) {
  console.error('Erreur import MessageThread:', error);
  MessageThread = () => <div>Erreur: MessageThread</div>;
}

try {
  DocumentUploader = require('./DocumentUploader/DocumentUploader').default;
} catch (error) {
  console.error('Erreur import DocumentUploader:', error);
  DocumentUploader = () => <div>Erreur: DocumentUploader</div>;
}

try {
  SearchInterface = require('./SearchInterface/SearchInterface').default;
} catch (error) {
  console.error('Erreur import SearchInterface:', error);
  SearchInterface = () => <div>Erreur: SearchInterface - {error.message}</div>;
}

try {
  CommandPanel = require('./CommandPanel/CommandPanel').default;
} catch (error) {
  console.error('Erreur import CommandPanel:', error);
  CommandPanel = () => <div>Erreur: CommandPanel - {error.message}</div>;
}

const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [unreadCount, setUnreadCount] = useState(0);
  const containerRef = useRef(null);

  // Configuration des onglets
  const tabItems = [
    {
      key: 'chat',
      label: (
        <span>
          <MessageOutlined />
          Chat
        </span>
      ),
      children: (
        <ErrorBoundary>
          <MessageThread />
        </ErrorBoundary>
      ),
    },
    {
      key: 'conversations',
      label: (
        <span>
          <FileTextOutlined />
          Conversations
        </span>
      ),
      children: (
        <ErrorBoundary>
          <ConversationList />
        </ErrorBoundary>
      ),
    },
    {
      key: 'documents',
      label: (
        <span>
          <UploadOutlined />
          Documents
        </span>
      ),
      children: (
        <ErrorBoundary>
          <DocumentUploader />
        </ErrorBoundary>
      ),
    },
    {
      key: 'search',
      label: (
        <span>
          <SearchOutlined />
          Recherche
        </span>
      ),
      children: (
        <ErrorBoundary>
          <SearchInterface />
        </ErrorBoundary>
      ),
    },
    {
      key: 'commands',
      label: (
        <span>
          <CodeOutlined />
          Commandes
        </span>
      ),
      children: (
        <ErrorBoundary>
          <CommandPanel />
        </ErrorBoundary>
      ),
    },
  ];

  if (!isOpen) {
    return (
      <div className="chatbot-container">
        <Tooltip title="AI Assistant Hub" placement="left">
          <Button
            type="primary"
            shape="circle"
            size="large"
            icon={<RobotOutlined />}
            onClick={() => setIsOpen(true)}
            style={{
              position: 'fixed',
              bottom: '20px',
              right: '20px',
              zIndex: 1000,
              width: '60px',
              height: '60px',
              fontSize: '24px',
            }}
          >
            {unreadCount > 0 && (
              <Badge
                count={unreadCount}
                style={{
                  position: 'absolute',
                  top: '-5px',
                  right: '-5px',
                }}
              />
            )}
          </Button>
        </Tooltip>
      </div>
    );
  }

  return (
    <div className="chatbot-container" ref={containerRef}>
      <Card
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '400px',
          height: '600px',
          zIndex: 1000,
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
        }}
        bodyStyle={{ padding: 0, height: '100%' }}
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>
              <RobotOutlined style={{ marginRight: '8px' }} />
              AI Assistant Hub
            </span>
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={() => setIsOpen(false)}
            />
          </div>
        }
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          size="small"
          style={{ height: '100%' }}
          tabBarStyle={{ margin: 0, padding: '0 16px' }}
        />
      </Card>
    </div>
  );
};

export default ChatBot;
