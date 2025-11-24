-- ============================================================================
-- SQL PARA CRIAR TABELA DE FILA DE MENSAGENS CLONADAS NO SUPABASE
-- ============================================================================
-- Execute este SQL no Supabase SQL Editor:
-- https://app.supabase.com/project/[SEU_PROJETO]/sql

-- Criar tabela de fila de mensagens clonadas
CREATE TABLE IF NOT EXISTS fila_mensagens_clonadas (
    id BIGSERIAL PRIMARY KEY,
    mensagem_original TEXT,
    mensagem_com_afiliado TEXT,
    imagem_url TEXT,
    grupo_origem VARCHAR(100),
    grupo_origem_nome VARCHAR(255),
    agendamento_envio TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'enviando', 'enviado', 'erro')),
    tentativas INTEGER DEFAULT 0,
    erro_mensagem TEXT,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    enviado_em TIMESTAMPTZ
);

-- Criar indices para performance
CREATE INDEX IF NOT EXISTS idx_fila_status ON fila_mensagens_clonadas(status);
CREATE INDEX IF NOT EXISTS idx_fila_agendamento ON fila_mensagens_clonadas(agendamento_envio);
CREATE INDEX IF NOT EXISTS idx_fila_status_agendamento ON fila_mensagens_clonadas(status, agendamento_envio);

-- Habilitar RLS (Row Level Security) - opcional, desabilite se nao precisar
ALTER TABLE fila_mensagens_clonadas ENABLE ROW LEVEL SECURITY;

-- Politica para permitir todas as operacoes (ajuste conforme necessario)
CREATE POLICY "Allow all operations on fila_mensagens_clonadas" ON fila_mensagens_clonadas
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- FUNCAO PARA LIMPAR MENSAGENS ANTIGAS AUTOMATICAMENTE (OPCIONAL)
-- ============================================================================

-- Funcao para limpar mensagens enviadas com mais de 7 dias
CREATE OR REPLACE FUNCTION limpar_fila_antigas()
RETURNS void AS $$
BEGIN
    DELETE FROM fila_mensagens_clonadas
    WHERE status = 'enviado'
    AND enviado_em < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VERIFICAR SE A TABELA FOI CRIADA
-- ============================================================================
-- SELECT * FROM fila_mensagens_clonadas LIMIT 10;
