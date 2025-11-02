-- ============================================================================
-- Script de Inicialización de Base de Datos
-- API Créditos PyMEs
-- ============================================================================
-- Este script inicializa completamente la base de datos con:
-- 1. Tipos ENUM personalizados
-- 2. Tablas con constraints y checks
-- 3. Índices para optimización de queries
-- 4. Funciones PL/pgSQL
-- 5. Triggers para automatización
--
-- Ejecutar con privilegios de superusuario o role con permisos CREATE
-- ============================================================================

-- ============================================================================
-- 1. TIPOS ENUM
-- ============================================================================

-- Roles de usuario
CREATE TYPE user_role AS ENUM (
  'applicant',      -- Solicitante (dueño de empresa que solicita créditos)
  'operator',       -- Operador (revisa, aprueba o rechaza solicitudes)
  'admin'           -- Administrador (acceso total)
);

-- Estados de solicitudes de crédito
CREATE TYPE credit_application_status AS ENUM (
  'draft',          -- Borrador (no enviado)
  'pending',        -- Pendiente de revisión
  'in_review',      -- En revisión por operador
  'approved',       -- Aprobada
  'rejected'        -- Rechazada
);

-- Propósitos de solicitudes de crédito
CREATE TYPE credit_application_purpose AS ENUM (
  'working_capital',
  'equipment',
  'expansion',
  'inventory',
  'refinancing',
  'other'
);

-- Tipos de documento
CREATE TYPE document_type AS ENUM (
  'tax_return',           -- Declaración de impuestos
  'financial_statement',  -- Estados financieros
  'id_document',          -- Documento de identidad
  'business_license',     -- Licencia comercial
  'bank_statement',       -- Estado de cuenta bancario
  'other'                 -- Otro tipo de documento
);

-- Estados de firma de documentos
CREATE TYPE signature_status AS ENUM (
  'unsigned',       -- Sin firmar
  'pending',        -- Pendiente de firma
  'signed',         -- Firmado
  'declined'        -- Firma rechazada
);

-- Estados de documento (revisión/ciclo de vida del archivo)
CREATE TYPE document_status AS ENUM (
  'pending',        -- Solicitado por operador (placeholder)
  'approved',       -- Aprobado por operador
  'rejected',       -- Rechazado por operador
  'uploaded',       -- Subido por el usuario
  'requested'       -- Solicitado/requerido
);

-- ============================================================================
-- 2. TABLAS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabla: profiles
-- Perfiles de usuario que complementan auth.users de Supabase Auth
-- ----------------------------------------------------------------------------
CREATE TABLE public.profiles (
  id UUID NOT NULL,
  email VARCHAR(255) NOT NULL,
  first_name VARCHAR(100) NULL,
  last_name VARCHAR(100) NULL,
  role user_role NOT NULL DEFAULT 'applicant'::user_role,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT profiles_pkey PRIMARY KEY (id),
  CONSTRAINT profiles_email_key UNIQUE (email),
  CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE
);

COMMENT ON TABLE public.profiles IS 'Perfiles de usuarios, complementa auth.users';
COMMENT ON COLUMN public.profiles.id IS 'ID único que referencia a auth.users(id)';
COMMENT ON COLUMN public.profiles.email IS 'Email verificado (sincronizado con auth.users(email))';
COMMENT ON COLUMN public.profiles.first_name IS 'Nombre(s) del usuario';
COMMENT ON COLUMN public.profiles.last_name IS 'Apellido(s) del usuario';
COMMENT ON COLUMN public.profiles.role IS 'Rol del usuario en el sistema (enum user_role)';

-- ----------------------------------------------------------------------------
-- Tabla: companies
-- Empresas (PyMEs) registradas en el sistema
-- ----------------------------------------------------------------------------
CREATE TABLE public.companies (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  legal_name VARCHAR(255) NOT NULL,
  tax_id VARCHAR(50) NOT NULL,
  contact_email VARCHAR(255) NOT NULL,
  contact_phone VARCHAR(20) NOT NULL,
  address JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT companies_pkey PRIMARY KEY (id),
  CONSTRAINT companies_tax_id_key UNIQUE (tax_id),
  CONSTRAINT companies_user_id_key UNIQUE (user_id),
  CONSTRAINT companies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE
);

COMMENT ON TABLE public.companies IS 'Empresas registradas que solicitan créditos';
COMMENT ON COLUMN public.companies.user_id IS 'Usuario representante (único por empresa)';
COMMENT ON COLUMN public.companies.legal_name IS 'Nombre legal completo de la empresa';
COMMENT ON COLUMN public.companies.tax_id IS 'RNC/RFC/RUT/NIF único de la empresa';
COMMENT ON COLUMN public.companies.contact_email IS 'Email del contacto principal';
COMMENT ON COLUMN public.companies.contact_phone IS 'Teléfono del contacto principal';
COMMENT ON COLUMN public.companies.address IS 'Dirección completa en formato JSON';

-- ----------------------------------------------------------------------------
-- Tabla: credit_applications
-- Solicitudes de crédito de empresas
-- ----------------------------------------------------------------------------
CREATE TABLE public.credit_applications (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL,
  requested_amount NUMERIC(15, 2) NOT NULL,
  purpose credit_application_purpose NOT NULL,
  purpose_other TEXT NULL,
  term_months INTEGER NOT NULL,
  status credit_application_status NOT NULL DEFAULT 'pending'::credit_application_status,
  risk_score NUMERIC(5, 2) NULL,
  approved_amount NUMERIC(15, 2) NULL,
  interest_rate NUMERIC(5, 2) NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT credit_applications_pkey PRIMARY KEY (id),
  CONSTRAINT credit_applications_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE,
  CONSTRAINT credit_applications_requested_amount_check CHECK (requested_amount > 0::numeric),
  CONSTRAINT credit_applications_term_months_check CHECK (term_months >= 1 AND term_months <= 360),
  CONSTRAINT credit_applications_risk_score_check CHECK (risk_score >= 0::numeric AND risk_score <= 100::numeric),
  CONSTRAINT credit_applications_approved_amount_check CHECK (approved_amount IS NULL OR approved_amount >= 0::numeric),
  CONSTRAINT credit_applications_interest_rate_check CHECK (interest_rate IS NULL OR interest_rate >= 0::numeric),
  CONSTRAINT check_purpose_other CHECK (purpose <> 'other'::credit_application_purpose OR purpose_other IS NOT NULL)
);

COMMENT ON TABLE public.credit_applications IS 'Solicitudes de crédito de empresas';
COMMENT ON COLUMN public.credit_applications.company_id IS 'Empresa que solicita el crédito';
COMMENT ON COLUMN public.credit_applications.requested_amount IS 'Monto solicitado en la moneda local';
COMMENT ON COLUMN public.credit_applications.purpose IS 'Propósito del crédito';
COMMENT ON COLUMN public.credit_applications.purpose_other IS 'Otro propósito (si aplica)';
COMMENT ON COLUMN public.credit_applications.term_months IS 'Plazo solicitado en meses';
COMMENT ON COLUMN public.credit_applications.status IS 'Estado actual de la solicitud';
COMMENT ON COLUMN public.credit_applications.risk_score IS 'Puntaje de riesgo asignado durante la evaluación';
COMMENT ON COLUMN public.credit_applications.approved_amount IS 'Monto aprobado (si aplica)';
COMMENT ON COLUMN public.credit_applications.interest_rate IS 'Tasa de interés anual aplicada (si aplica)';

-- ----------------------------------------------------------------------------
-- Tabla: documents
-- Documentos asociados a solicitudes (auto-populada desde storage)
-- ----------------------------------------------------------------------------
CREATE TABLE public.documents (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  application_id UUID NULL,
  storage_path VARCHAR NULL,
  bucket_name VARCHAR(100) NULL,
  file_name VARCHAR(255) NULL,
  file_size INTEGER NULL,
  mime_type VARCHAR(100) NULL,
  document_type document_type NULL,
  extra_metadata JSON NULL,
  signature_request_id VARCHAR(255) NULL,
  signature_status signature_status NOT NULL DEFAULT 'unsigned'::signature_status,
  signed_at TIMESTAMP NULL,
  signed_file_path VARCHAR NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  status document_status NOT NULL DEFAULT 'pending'::document_status,
  CONSTRAINT documents_pkey PRIMARY KEY (id),
  CONSTRAINT fk_documents_application FOREIGN KEY (application_id) REFERENCES public.credit_applications(id) ON DELETE CASCADE,
  CONSTRAINT fk_documents_user FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE
);

COMMENT ON TABLE public.documents IS 'Documentos subidos vía Storage, auto-registrados con trigger';
COMMENT ON COLUMN public.documents.user_id IS 'Usuario que subió el documento';
COMMENT ON COLUMN public.documents.application_id IS 'Solicitud asociada (validada en trigger)';
COMMENT ON COLUMN public.documents.storage_path IS 'Ruta completa en storage (bucket/path)';
COMMENT ON COLUMN public.documents.extra_metadata IS 'Metadata adicional flexible (ej: requires_signature)';
COMMENT ON COLUMN public.documents.signature_request_id IS 'ID de solicitud de firma en HelloSign/DocuSign';
COMMENT ON COLUMN public.documents.signature_status IS 'Estado de firma: unsigned, pending, signed, declined';
COMMENT ON COLUMN public.documents.signed_file_path IS 'Ruta del archivo firmado en storage';

CREATE INDEX IF NOT EXISTS ix_documents_id ON public.documents USING btree (id);
CREATE INDEX IF NOT EXISTS ix_documents_application_id ON public.documents USING btree (application_id);
CREATE INDEX IF NOT EXISTS ix_documents_user_id ON public.documents USING btree (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_documents_storage_path ON public.documents USING btree (storage_path);
CREATE INDEX IF NOT EXISTS idx_documents_status ON public.documents USING btree (status);
CREATE INDEX IF NOT EXISTS idx_docs_status ON public.documents USING btree (status);

-- ============================================================================
-- 3. FUNCIONES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Función: custom_access_token_hook
-- Agrega custom claims al JWT (user_role desde profiles)
-- Configurar en Supabase Dashboard > Authentication > JWT Claims
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    claims jsonb;
    user_role public.user_role;
BEGIN
    -- Obtener el rol del usuario desde profiles
    SELECT role INTO user_role
    FROM public.profiles
    WHERE id = (event->>'user_id')::uuid;

    claims := event->'claims';

    IF user_role IS NOT NULL THEN
        claims := jsonb_set(claims, '{user_role}', to_jsonb(user_role));
    ELSE
        claims := jsonb_set(claims, '{user_role}', 'null');
    END IF;

    event := jsonb_set(event, '{claims}', claims);

    RETURN event;
END;
$$;

GRANT USAGE ON SCHEMA public TO supabase_auth_admin;
GRANT EXECUTE ON FUNCTION public.custom_access_token_hook TO supabase_auth_admin;
REVOKE EXECUTE ON FUNCTION public.custom_access_token_hook FROM authenticated, anon, public;
GRANT ALL ON TABLE public.profiles TO supabase_auth_admin;

-- ----------------------------------------------------------------------------
-- Función: handle_auth_user_created
-- Crea perfil y empresa automáticamente después del registro
-- Requiere raw_user_meta_data con: first_name, last_name, company
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_auth_user_created()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE 
  md jsonb := NEW.raw_user_meta_data;
BEGIN
  -- Validar que existan los metadatos requeridos
  IF md IS NULL
     OR md->>'first_name' IS NULL
     OR md->>'last_name' IS NULL
     OR NOT (md ? 'company') THEN
    RAISE EXCEPTION 'Faltan metadatos requeridos (first_name, last_name, company)';
  END IF;

  -- Crear perfil de usuario
  INSERT INTO public.profiles (id, email, first_name, last_name, role)
  VALUES (
    NEW.id,
    NEW.email,
    md->>'first_name',
    md->>'last_name',
    'applicant'
  );

  -- Crear empresa asociada
  INSERT INTO public.companies (user_id, legal_name, tax_id, contact_email, contact_phone, address)
  VALUES (
    NEW.id,
    md->'company'->>'legal_name',
    md->'company'->>'tax_id',
    COALESCE(md->'company'->>'contact_email', NEW.email),
    md->'company'->>'contact_phone',
    COALESCE((md->'company'->'address')::jsonb, '{}'::jsonb)
  );

  RETURN NEW;
END;
$$;

-- ----------------------------------------------------------------------------
-- Función: handle_storage_upload
-- Crea registro en documents cuando se sube archivo a storage
-- Extrae metadata (user_id, application_id, document_type) y valida permisos
-- Soporta placeholders: si viene document_id, actualiza el registro existente
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_storage_upload()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  md jsonb := NEW.metadata;
  umd jsonb := NEW.user_metadata;
  v_user_id uuid;
  v_application_id uuid;
  v_document_type text;
  v_application_company_id uuid;
  v_user_company_id uuid;
  v_document_id uuid;
  v_conflict_id uuid;
  v_user_role text;
  v_requires_signature boolean;
BEGIN
  -- DEBUG: Log de entrada
  RAISE NOTICE 'handle_storage_upload - Procesando: name=%, bucket=%, metadata=%, user_metadata=%', 
    NEW.name, NEW.bucket_id, md::text, umd::text;

  -- Solo procesar si hay user_metadata con user_id
  IF umd IS NULL THEN
    RAISE NOTICE 'user_metadata es NULL, saltando procesamiento';
    RETURN NEW;
  END IF;

  IF umd->>'user_id' IS NULL THEN
    RAISE NOTICE 'user_metadata.user_id es NULL, saltando procesamiento. user_metadata=%', umd::text;
    RETURN NEW;
  END IF;

  -- Extraer user_id
  BEGIN
    v_user_id := (umd->>'user_id')::uuid;
    RAISE NOTICE 'user_id extraído: %', v_user_id;
  EXCEPTION
    WHEN OTHERS THEN
      RAISE EXCEPTION 'Error convirtiendo user_id a UUID: %. user_metadata=%', SQLERRM, umd::text;
  END;

  -- Extraer application_id (opcional)
  BEGIN
    v_application_id := (umd->>'application_id')::uuid;
    RAISE NOTICE 'application_id extraído: %', v_application_id;
  EXCEPTION
    WHEN OTHERS THEN
      RAISE NOTICE 'application_id no es UUID válido o está ausente: %', SQLERRM;
      v_application_id := NULL;
  END;

  -- Extraer document_type
  v_document_type := umd->>'document_type';
  RAISE NOTICE 'document_type extraído (texto): %', v_document_type;

  -- Validar requires_signature: solo operator/admin pueden usarlo
  IF umd ? 'requires_signature' THEN
    v_requires_signature := (umd->>'requires_signature')::boolean;
    
    IF v_requires_signature = true THEN
      -- Obtener user_role del JWT (no 'role', que siempre es 'authenticated')
      v_user_role := COALESCE(
        NULLIF(current_setting('request.jwt.claims', true), '')::jsonb->>'user_role',
        'applicant'
      );
      
      RAISE NOTICE 'requires_signature=true detectado. user_role del JWT: %', v_user_role;
      
      -- Solo operator y admin pueden marcar documentos para firma
      IF v_user_role NOT IN ('operator', 'admin') THEN
        RAISE EXCEPTION 'PERMISO DENEGADO: Solo operadores y administradores pueden usar requires_signature=true. user_role actual: %', v_user_role;
      END IF;
      
      RAISE NOTICE 'Validación de permisos exitosa para requires_signature';
    END IF;
  END IF;

  -- Si viene document_id, intentar actualizar documento existente (placeholder)
  IF umd ? 'document_id' THEN
    BEGIN
      v_document_id := (umd->>'document_id')::uuid;
      RAISE NOTICE 'document_id recibido en user_metadata: %', v_document_id;
    EXCEPTION
      WHEN OTHERS THEN
        RAISE NOTICE 'document_id presente pero no es UUID válido: %', SQLERRM;
        v_document_id := NULL;
    END;

    IF v_document_id IS NOT NULL THEN
      -- Buscar documento existente
      SELECT id INTO v_conflict_id FROM public.documents WHERE id = v_document_id;
      
      IF v_conflict_id IS NOT NULL THEN
        -- Actualizar el documento existente con los metadatos de storage
        UPDATE public.documents
        SET
          storage_path = NEW.name,
          bucket_name = NEW.bucket_id,
          file_name = COALESCE(split_part(NEW.name, '/', -1), NEW.name),
          file_size = (md->>'size')::integer,
          mime_type = COALESCE(md->>'mimetype', md->>'contentType'),
          status = 'uploaded'::document_status,
          updated_at = NOW()
        WHERE id = v_document_id;

        RAISE NOTICE 'Documento % actualizado y marcado como uploaded', v_document_id;
        RETURN NEW;
      ELSE
        RAISE NOTICE 'document_id % no encontrado en public.documents, continuará flujo de inserción', v_document_id;
      END IF;
    END IF;
  END IF;

  -- Si hay application_id, validar que pertenezca a la empresa del usuario
  IF v_application_id IS NOT NULL THEN
    RAISE NOTICE 'Validando application_id % para user_id %', v_application_id, v_user_id;

    -- Obtener company_id de la solicitud
    SELECT company_id INTO v_application_company_id
    FROM public.credit_applications
    WHERE id = v_application_id;

    IF v_application_company_id IS NULL THEN
      RAISE EXCEPTION 'Solicitud % no encontrada en credit_applications', v_application_id;
    END IF;
    RAISE NOTICE 'Solicitud pertenece a company_id: %', v_application_company_id;

    -- Obtener company_id del usuario
    SELECT id INTO v_user_company_id
    FROM public.companies
    WHERE user_id = v_user_id;

    IF v_user_company_id IS NULL THEN
      RAISE EXCEPTION 'Usuario % no tiene empresa registrada en companies', v_user_id;
    END IF;
    RAISE NOTICE 'Usuario pertenece a company_id: %', v_user_company_id;

    -- Validar que coincidan
    IF v_application_company_id != v_user_company_id THEN
      RAISE EXCEPTION 'VALIDACIÓN FALLIDA: La solicitud % (company %) no pertenece al usuario % (company %)', 
        v_application_id, v_application_company_id, v_user_id, v_user_company_id;
    END IF;
    RAISE NOTICE 'Validación exitosa: solicitud y usuario pertenecen a la misma empresa';
  ELSE
    RAISE NOTICE 'No hay application_id, saltando validación de empresa';
  END IF;

  -- Crear registro en documents
  RAISE NOTICE 'Insertando en documents: user_id=%, application_id=%, path=%, bucket=%, file_name=%, size=%, mime=%, type=%',
    v_user_id, v_application_id, NEW.name, NEW.bucket_id, 
    COALESCE(split_part(NEW.name, '/', -1), NEW.name),
    (md->>'size')::integer, COALESCE(md->>'mimetype', md->>'contentType'), v_document_type;

  INSERT INTO public.documents (
    user_id,
    application_id,
    storage_path,
    bucket_name,
    file_name,
    file_size,
    mime_type,
    document_type,
    status,
    extra_metadata
  )
  VALUES (
    v_user_id,
    v_application_id,
    NEW.name,
    NEW.bucket_id,
    COALESCE(split_part(NEW.name, '/', -1), NEW.name),
    (md->>'size')::integer,
    COALESCE(md->>'mimetype', md->>'contentType'),
    v_document_type::document_type,
    'uploaded'::document_status,
    -- Copiar requires_signature desde user_metadata a extra_metadata
    CASE 
      WHEN umd ? 'requires_signature' THEN 
        json_build_object('requires_signature', (umd->>'requires_signature')::boolean)::json
      ELSE NULL
    END
  )
  ON CONFLICT (storage_path) DO UPDATE
  SET
    file_size = EXCLUDED.file_size,
    mime_type = EXCLUDED.mime_type,
    updated_at = NOW();

  RAISE NOTICE 'Documento insertado/actualizado exitosamente';
  RETURN NEW;

EXCEPTION
  WHEN OTHERS THEN
    -- Lanzar el error para debugging
    RAISE EXCEPTION 'ERROR en handle_storage_upload: %. SQLSTATE: %. Contexto: user_id=%, application_id=%, path=%', 
      SQLERRM, SQLSTATE, v_user_id, v_application_id, NEW.name;
END;
$$;

-- ----------------------------------------------------------------------------
-- Función: update_updated_at_column
-- Actualiza automáticamente la columna updated_at en cada UPDATE
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. TRIGGERS
-- ============================================================================

-- Trigger: Crear perfil y empresa después de registro en auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_auth_user_created();

-- Trigger: Registrar documento automáticamente al subir a storage
DROP TRIGGER IF EXISTS on_storage_object_created ON storage.objects;
CREATE TRIGGER on_storage_object_created
  AFTER INSERT ON storage.objects
  FOR EACH ROW EXECUTE FUNCTION public.handle_storage_upload();

-- Trigger: Actualizar updated_at en profiles
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger: Actualizar updated_at en companies
CREATE TRIGGER update_companies_updated_at
  BEFORE UPDATE ON public.companies
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger: Actualizar updated_at en credit_applications
CREATE TRIGGER update_credit_applications_updated_at
  BEFORE UPDATE ON public.credit_applications
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger: Actualizar updated_at en documents
CREATE TRIGGER update_documents_updated_at
  BEFORE UPDATE ON public.documents
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
-- La base de datos está lista para ser usada por la API.
-- 
-- IMPORTANTE: Este script refleja el esquema ACTUAL en producción (Supabase).
-- 
-- Notas importantes:
-- 1. Configurar custom_access_token_hook en Supabase Dashboard:
--    Authentication > Hooks > Custom Access Token Hook
--    Función: public.custom_access_token_hook
--
-- 2. Configurar políticas RLS (Row Level Security) si es necesario
--    Ver carpeta db/policies/ para ejemplos
--
-- 3. El trigger handle_auth_user_created requiere raw_user_meta_data
--    durante el registro con: first_name, last_name, company
--
-- 4. El trigger handle_storage_upload requiere user_metadata en uploads
--    con: user_id (obligatorio), application_id, document_type
--
-- 5. Diferencias respecto al modelo Python (SQLModel):
--    - credit_applications.status: default 'pending' (en Python se usa 'draft')
--    - documents.file_size: INTEGER en BD vs BIGINT en código
--    - documents.signed_at: TIMESTAMP en BD vs TIMESTAMPTZ en código
--    - documents.extra_metadata: JSON en BD vs JSONB en código
--    - Faltan columnas en credit_applications: operator_id, reviewed_at, review_notes
--    - Falta constraint check_purpose_other en credit_applications
--
-- ============================================================================
