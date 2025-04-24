-- Configuración inicial
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

-- Usar la base de datos correcta
USE `sistema_ganade`;

-- Estructura de la tabla `usuarios`
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `rol` varchar(20) NOT NULL DEFAULT 'usuario',
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Estructura de la tabla `animales`
CREATE TABLE `animales` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `categoria` varchar(50) NOT NULL,
  `raza` varchar(50) NOT NULL,
  `fecha_nacimiento` date NOT NULL,
  `peso` decimal(10,2) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Estructura de la tabla `vacuna`
CREATE TABLE `vacuna` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `animal_id` int(11) NOT NULL,
  `tipo_vacuna` varchar(100) NOT NULL,
  `fecha_aplicacion` date NOT NULL,
  `fecha_proxima` date DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `animal_id` (`animal_id`),
  CONSTRAINT `vacuna_ibfk_1` FOREIGN KEY (`animal_id`) REFERENCES `animales` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Estructura de la tabla `gestaciones`
CREATE TABLE `gestaciones` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `animal_id` int(11) NOT NULL,
  `fecha_inseminacion` date NOT NULL,
  `tipo_inseminacion` varchar(50) NOT NULL,
  `semental` varchar(100) NOT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'En Gestación',
  `observaciones` text DEFAULT NULL,
  `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `animal_id` (`animal_id`),
  CONSTRAINT `gestaciones_ibfk_1` FOREIGN KEY (`animal_id`) REFERENCES `animales` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Estructura de la tabla `config_alarmas`
CREATE TABLE `config_alarmas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_alarma` varchar(50) NOT NULL,
  `dias_anticipacion` int(11) NOT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'activa',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertar configuración inicial de alarmas
INSERT INTO `config_alarmas` (`tipo_alarma`, `dias_anticipacion`, `estado`) VALUES
('vacunacion', 7, 'activa'),
('parto', 14, 'activa'),
('desparasitacion', 7, 'activa');

-- Usuario administrador inicial (contraseña: admin123)
INSERT INTO `usuarios` (`nombre`, `email`, `password`, `rol`) VALUES
('Administrador', 'admin@sistema.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFpxYR.N6.WCF.q', 'admin');
