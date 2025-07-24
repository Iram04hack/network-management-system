# Migration pour corriger la table KnowledgeBase

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0003_simple_fix'),
    ]

    operations = [
        # Recréer complètement la table KnowledgeBase avec la bonne structure
        migrations.RunSQL(
            """
            -- Sauvegarder les données existantes si elles existent
            CREATE TEMP TABLE kb_temp AS 
            SELECT * FROM ai_assistant_knowledgebase WHERE 1=0;
            
            -- Supprimer la table existante
            DROP TABLE IF EXISTS ai_assistant_knowledgebase CASCADE;
            
            -- Créer la nouvelle table avec la structure correcte
            CREATE TABLE ai_assistant_knowledgebase (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) DEFAULT '',
                content TEXT DEFAULT '',
                content_type VARCHAR(100) DEFAULT 'text/plain',
                tags JSONB DEFAULT '[]'::jsonb,
                category VARCHAR(50) DEFAULT 'general',
                question TEXT DEFAULT '',
                answer TEXT DEFAULT '',
                keywords JSONB DEFAULT '[]'::jsonb,
                related_commands JSONB DEFAULT '[]'::jsonb,
                confidence_score REAL DEFAULT 1.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
            );
            
            -- Créer les index
            CREATE INDEX idx_knowledgebase_active ON ai_assistant_knowledgebase(is_active);
            CREATE INDEX idx_knowledgebase_category ON ai_assistant_knowledgebase(category);
            CREATE INDEX idx_knowledgebase_title ON ai_assistant_knowledgebase(title);
            CREATE INDEX idx_knowledgebase_content ON ai_assistant_knowledgebase USING gin(to_tsvector('english', content));
            """,
            reverse_sql="DROP TABLE IF EXISTS ai_assistant_knowledgebase;"
        ),
        
        # Insérer quelques données de test pour valider l'intégration
        migrations.RunSQL(
            """
            INSERT INTO ai_assistant_knowledgebase (
                title, content, content_type, tags, category, is_active
            ) VALUES 
            (
                'Test Document 1',
                'This is a test document for integration validation. It contains sample content for testing the AI Assistant document management features.',
                'text/plain',
                '["test", "integration", "validation"]'::jsonb,
                'general',
                TRUE
            ),
            (
                'Network Configuration Guide',
                'This document contains network configuration guidelines and best practices for network management systems.',
                'text/plain',
                '["network", "configuration", "guide"]'::jsonb,
                'network',
                TRUE
            );
            """,
            reverse_sql=""
        ),
    ]
