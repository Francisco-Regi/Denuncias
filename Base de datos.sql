-- ===========================
-- TABLA DE USUARIOS
-- ===========================
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    correo TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL,
    telefono TEXT,
    curp TEXT,
    acepta_terminos INTEGER NOT NULL CHECK (acepta_terminos IN (0, 1))
);

-- ===========================
-- TABLA DE DENUNCIAS
-- ===========================
CREATE TABLE IF NOT EXISTS denuncias (
    id_denuncia INTEGER PRIMARY KEY AUTOINCREMENT,

    -- FK si es denuncia digital (NULL en anónima)
    id_usuario INTEGER,

    -- Tipo de denuncia: 'anonima' o 'digital'
    tipo_denuncia TEXT NOT NULL CHECK (
        tipo_denuncia IN ('anonima', 'digital')
    ),

    -- Categoría del incidente
    categoria TEXT NOT NULL CHECK (
        categoria IN (
            'Seguridad vial',
            'Seguridad civil',
            'Seguridad infantil',
            'Seguridad médica',
            'Seguridad policiaca',
            'Ciberseguridad'
        )
    ),

    -- Ubicación
    latitud TEXT,
    longitud TEXT,
    direccion TEXT,

    -- Fecha y hora del incidente
    fecha_hora TEXT NOT NULL, -- formato ISO

    -- Placa del vehículo (solo si aplica)
    placa_vehiculo TEXT,

    -- Descripción general del incidente
    descripcion TEXT NOT NULL,

    -- Folio único generado automáticamente
    folio TEXT UNIQUE NOT NULL,

    -- Estado del caso
    estado TEXT DEFAULT 'Recibida',

    -- Seguimiento del caso
    descripcion_seguimiento TEXT,

    -- Nombre del personal que atendió el caso
    atendido_por TEXT,

    -- Cargo del personal
    cargo TEXT,

    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- ===========================
-- TABLA DE EVIDENCIAS
-- ===========================
CREATE TABLE IF NOT EXISTS evidencias (
    id_evidencia INTEGER PRIMARY KEY AUTOINCREMENT,

    -- FK a denuncia
    id_denuncia INTEGER NOT NULL,

    -- Ruta o nombre del archivo
    archivo TEXT NOT NULL,

    -- Tipo de archivo (opcional): imagen, video, documento
    tipo TEXT,

    FOREIGN KEY (id_denuncia) REFERENCES denuncias(id_denuncia)
);
