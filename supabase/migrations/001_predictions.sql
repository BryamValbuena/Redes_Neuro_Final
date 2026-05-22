-- PlantAI — tabla de historial de predicciones
-- Ejecutar en: Supabase Dashboard → SQL Editor → New query → Run

CREATE TABLE IF NOT EXISTS public.predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  image_name TEXT NOT NULL,
  predicted_class TEXT NOT NULL,
  confidence NUMERIC(6, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
  processing_time_ms NUMERIC(10, 2) NOT NULL CHECK (processing_time_ms >= 0),
  estimated_processing_usage NUMERIC(12, 4),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.predictions IS 'Historial de diagnósticos PlantAI por usuario (JWT username)';
COMMENT ON COLUMN public.predictions.user_id IS 'Usuario de la app (login JWT, ej. admin)';
COMMENT ON COLUMN public.predictions.estimated_processing_usage IS 'Unidad estimada: KB imagen + segundos de inferencia';

CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON public.predictions (user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON public.predictions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_user_created ON public.predictions (user_id, created_at DESC);

ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;

-- Sin políticas públicas: el backend usa service_role (bypass RLS).
-- Cuando migres a Supabase Auth, añade políticas por auth.uid().
