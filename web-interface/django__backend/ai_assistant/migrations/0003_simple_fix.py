# Migration simple pour corriger les erreurs d'intégration

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0002_fix_integration'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Créer les tables manquantes avec SQL simple
        migrations.RunSQL(
            """
            -- Créer ConversationMetrics si elle n'existe pas
            CREATE TABLE IF NOT EXISTS ai_assistant_conversationmetrics (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER NOT NULL UNIQUE,
                total_messages INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                average_response_time REAL DEFAULT 0.0,
                successful_commands INTEGER DEFAULT 0,
                failed_commands INTEGER DEFAULT 0,
                user_satisfaction_score REAL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS ai_assistant_conversationmetrics;"
        ),
        
        migrations.RunSQL(
            """
            -- Créer APIUsage si elle n'existe pas
            CREATE TABLE IF NOT EXISTS ai_assistant_apiusage (
                id SERIAL PRIMARY KEY,
                model_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                request_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                cost DECIMAL(10,6) DEFAULT 0.0,
                date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS ai_assistant_apiusage;"
        ),
        
        # Ajouter les contraintes de clés étrangères après création
        migrations.RunSQL(
            """
            -- Ajouter les contraintes FK si elles n'existent pas
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'ai_assistant_conversationmetrics_conversation_id_fkey'
                ) THEN
                    ALTER TABLE ai_assistant_conversationmetrics 
                    ADD CONSTRAINT ai_assistant_conversationmetrics_conversation_id_fkey 
                    FOREIGN KEY (conversation_id) REFERENCES ai_assistant_conversation(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            reverse_sql=""
        ),
        
        # Créer les index pour les performances
        migrations.RunSQL(
            """
            CREATE INDEX IF NOT EXISTS idx_conversation_user ON ai_assistant_conversation(user_id);
            CREATE INDEX IF NOT EXISTS idx_message_conversation ON ai_assistant_message(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_message_created_at ON ai_assistant_message(created_at);
            """,
            reverse_sql=""
        ),
    ]
