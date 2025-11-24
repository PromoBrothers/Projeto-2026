-- ============================================================================
-- ADICIONAR COLUNAS DE CUPOM NA TABELA PROMOCOES
-- ============================================================================
-- Execute este SQL no Supabase SQL Editor para adicionar as colunas de cupom

-- Adicionar coluna cupom_info (armazena JSON com informações do cupom)
ALTER TABLE public.promocoes
ADD COLUMN IF NOT EXISTS cupom_info JSONB;

-- Adicionar coluna preco_com_cupom (armazena o preço final com desconto)
ALTER TABLE public.promocoes
ADD COLUMN IF NOT EXISTS preco_com_cupom DECIMAL(10,2);

-- Comentários
COMMENT ON COLUMN public.promocoes.cupom_info IS 'Informações do cupom aplicado (JSON: cupom_id, codigo, porcentagem, limite_valor)';
COMMENT ON COLUMN public.promocoes.preco_com_cupom IS 'Preço final do produto com cupom aplicado';

-- Índice para melhorar consultas de produtos com cupom
CREATE INDEX IF NOT EXISTS idx_promocoes_cupom_info ON public.promocoes USING GIN (cupom_info);
CREATE INDEX IF NOT EXISTS idx_promocoes_preco_com_cupom ON public.promocoes(preco_com_cupom) WHERE preco_com_cupom IS NOT NULL;

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

-- Verificar se as colunas foram criadas
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'promocoes'
AND column_name IN ('cupom_info', 'preco_com_cupom')
ORDER BY ordinal_position;

-- Exemplo de produto com cupom
-- UPDATE promocoes
-- SET
--     cupom_info = '{"cupom_id":"1","codigo":"VALEPROMO","porcentagem":10,"limite_valor":30}'::jsonb,
--     preco_com_cupom = 569.00
-- WHERE id = 'SEU_PRODUTO_ID';
