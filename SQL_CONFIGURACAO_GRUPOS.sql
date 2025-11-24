-- ============================================================================
-- SQL para criar tabela de configuração de grupos fixos
-- Execute este SQL no Supabase SQL Editor
-- ============================================================================

-- Criar tabela de grupos fixos para agendamentos automáticos
CREATE TABLE IF NOT EXISTS grupos_fixos_agendamento (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    grupo_id TEXT NOT NULL UNIQUE,
    grupo_nome TEXT NOT NULL,
    ativo BOOLEAN DEFAULT true,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Adicionar índice para busca rápida
CREATE INDEX IF NOT EXISTS idx_grupos_fixos_ativo ON grupos_fixos_agendamento(ativo);

-- Comentários para documentação
COMMENT ON TABLE grupos_fixos_agendamento IS 'Grupos do WhatsApp que receberão automaticamente os agendamentos';
COMMENT ON COLUMN grupos_fixos_agendamento.grupo_id IS 'ID do grupo WhatsApp (ex: 120363...@g.us)';
COMMENT ON COLUMN grupos_fixos_agendamento.grupo_nome IS 'Nome do grupo para exibição';
COMMENT ON COLUMN grupos_fixos_agendamento.ativo IS 'Se o grupo está ativo para receber mensagens';
