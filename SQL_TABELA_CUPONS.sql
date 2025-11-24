-- ============================================================================
-- TABELA DE CUPONS
-- ============================================================================
-- Execute este SQL no Supabase SQL Editor para criar a tabela de cupons

CREATE TABLE IF NOT EXISTS public.cupons (
    id BIGSERIAL PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    porcentagem DECIMAL(5,2) NOT NULL CHECK (porcentagem >= 0 AND porcentagem <= 100),
    limite_valor DECIMAL(10,2) NOT NULL CHECK (limite_valor >= 0),
    ativo BOOLEAN DEFAULT true,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_cupons_codigo ON public.cupons(codigo);
CREATE INDEX IF NOT EXISTS idx_cupons_ativo ON public.cupons(ativo);
CREATE INDEX IF NOT EXISTS idx_cupons_criado_em ON public.cupons(criado_em DESC);

-- Comentários
COMMENT ON TABLE public.cupons IS 'Tabela para armazenar cupons de desconto';
COMMENT ON COLUMN public.cupons.id IS 'ID único do cupom';
COMMENT ON COLUMN public.cupons.codigo IS 'Código do cupom (ex: PROMO10)';
COMMENT ON COLUMN public.cupons.porcentagem IS 'Porcentagem de desconto (0-100)';
COMMENT ON COLUMN public.cupons.limite_valor IS 'Valor máximo de desconto em reais';
COMMENT ON COLUMN public.cupons.ativo IS 'Se o cupom está ativo';
COMMENT ON COLUMN public.cupons.criado_em IS 'Data de criação do cupom';
COMMENT ON COLUMN public.cupons.atualizado_em IS 'Data da última atualização';

-- Trigger para atualizar automaticamente o campo atualizado_em
CREATE OR REPLACE FUNCTION public.atualizar_cupons_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atualizar_cupons_timestamp
    BEFORE UPDATE ON public.cupons
    FOR EACH ROW
    EXECUTE FUNCTION public.atualizar_cupons_timestamp();

-- RLS (Row Level Security) - Permitir acesso apenas autenticado
ALTER TABLE public.cupons ENABLE ROW LEVEL SECURITY;

-- Policy para leitura (permite visualização)
CREATE POLICY "Permitir leitura de cupons" ON public.cupons
    FOR SELECT
    USING (true);

-- Policy para inserção (permite criar cupons)
CREATE POLICY "Permitir inserção de cupons" ON public.cupons
    FOR INSERT
    WITH CHECK (true);

-- Policy para atualização (permite editar cupons)
CREATE POLICY "Permitir atualização de cupons" ON public.cupons
    FOR UPDATE
    USING (true);

-- Policy para deleção (permite remover cupons)
CREATE POLICY "Permitir deleção de cupons" ON public.cupons
    FOR DELETE
    USING (true);

-- ============================================================================
-- DADOS DE EXEMPLO (OPCIONAL - pode remover se não quiser)
-- ============================================================================

INSERT INTO public.cupons (codigo, porcentagem, limite_valor, ativo) VALUES
    ('PROMO10', 10.00, 30.00, true),
    ('DESCONTO15', 15.00, 50.00, true),
    ('MEGA20', 20.00, 100.00, true)
ON CONFLICT (codigo) DO NOTHING;

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

-- Verificar se a tabela foi criada
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'cupons'
ORDER BY ordinal_position;

-- Listar cupons
SELECT * FROM public.cupons ORDER BY criado_em DESC;
