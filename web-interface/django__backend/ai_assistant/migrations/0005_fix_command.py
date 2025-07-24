# Migration pour corriger la table Command

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0004_fix_knowledgebase'),
    ]

    operations = [
        # Recréer la table Command avec la structure correcte
        migrations.RunSQL(
            """
            -- Supprimer la table existante si elle existe
            DROP TABLE IF EXISTS ai_assistant_command CASCADE;
            
            -- Créer la nouvelle table avec la structure correcte
            CREATE TABLE ai_assistant_command (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                category VARCHAR(50) DEFAULT 'system',
                description TEXT DEFAULT '',
                command_template TEXT DEFAULT '',
                parameters JSONB DEFAULT '{}'::jsonb,
                required_permission VARCHAR(20) DEFAULT 'read',
                is_safe BOOLEAN DEFAULT TRUE,
                is_active BOOLEAN DEFAULT TRUE,
                timeout_seconds INTEGER DEFAULT 30,
                status VARCHAR(20) DEFAULT 'pending',
                result JSONB DEFAULT '{}'::jsonb,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Créer les index
            CREATE INDEX idx_command_category ON ai_assistant_command(category);
            CREATE INDEX idx_command_status ON ai_assistant_command(status);
            CREATE INDEX idx_command_active ON ai_assistant_command(is_active);
            """,
            reverse_sql="DROP TABLE IF EXISTS ai_assistant_command;"
        ),
        
        # Insérer quelques commandes de test
        migrations.RunSQL(
            """
            INSERT INTO ai_assistant_command (
                name, category, description, command_template, parameters, 
                required_permission, is_safe, is_active, status, result
            ) VALUES 
            (
                'test_command',
                'system',
                'Test command for integration validation',
                'echo "Test command executed"',
                '{}'::jsonb,
                'read',
                TRUE,
                TRUE,
                'completed',
                '{"message": "Test command executed successfully"}'::jsonb
            ),
            (
                'network_ping',
                'network',
                'Ping a network host',
                'ping -c 4 {target}',
                '{"target": {"type": "string", "required": true}}'::jsonb,
                'read',
                TRUE,
                TRUE,
                'pending',
                '{}'::jsonb
            );
            """,
            reverse_sql=""
        ),
    ]
