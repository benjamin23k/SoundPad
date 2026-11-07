# Xyron Soundpad

Soundboard de escritorio para Windows 10/11 con salida a micrófono virtual (VB-CABLE), inspirado funcionalmente en Soundpad de Leppsoft.

## Estado

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Fundamentos: estructura, ventana principal, tema, SQLite, logging, configuración | Implementada y probada |
| 2 | Soundboard: importación, reproducción, búsqueda, categorías | Núcleo implementado (importar, reproducir, pausar, detener, siguiente/anterior, volumen); falta probar el audio real en Windows |
| 3 | Audio virtual: dispositivos, micrófono, VB-CABLE, mezclador | Pendiente |
| 4 | Hotkeys globales | Pendiente |
| 5 | Audio avanzado | Pendiente |
| 6 | Grabador y editor | Pendiente |
| 7 | Perfiles, packs, temas | Pendiente |
| 8 | Distribución | Pendiente |

Los botones Headphones y Microphone y la pantalla Settings siguen deshabilitados hasta la Fase 3. Si `sounddevice` no puede abrir una salida de audio, los controles de reproducción quedan deshabilitados y la barra de estado indica "Audio engine: unavailable".

## Requisitos

- Python 3.12 o superior
- Windows 10/11 para el MVP completo (la interfaz y las pruebas de Fase 1 también corren en Linux/macOS)

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Probar a mano

```bash
python scripts/generate_test_sounds.py test_sounds
python main.py
```

En la app: File > Add Folder... y elige `test_sounds`, o arrastra los .wav a la tabla. Doble clic reproduce un sonido; selecciona varios y pulsa Enter para mezclarlos; Esc detiene todo, Espacio pausa o reanuda, Ctrl+Izquierda/Derecha cambia de sonido.

## Pruebas

```bash
set QT_QPA_PLATFORM=offscreen
python -m pytest
```

## Arquitectura

```text
src/soundpad/
├── app.py            arranque y composición
├── core/             rutas, configuración (Pydantic), logging
├── database/         modelos SQLAlchemy, sesión SQLite, repositorios
├── services/         casos de uso (LibraryService)
├── ui/
│   ├── components/   widgets reutilizables
│   ├── viewmodels/   modelos Qt (QAbstractTableModel + proxy)
│   ├── views/        ventana principal
│   └── theme/        paleta, QSS e iconos dibujados
├── audio/ hotkeys/ soundboard/ profiles/ system/   reservados para fases siguientes
└── utils/
```

Decisiones:

- La tabla usa `QTableView` + `QAbstractTableModel` + `QSortFilterProxyModel`; la búsqueda y el ordenamiento ocurren en el proxy.
- La UI solo habla con servicios; los servicios usan repositorios; nada de la UI toca SQLAlchemy.
- "My Sounds" y "Uncategorized" son vistas virtuales; las categorías reales viven en la base de datos.
- La configuración se guarda de forma atómica en `data/settings.json`; un archivo corrupto se respalda como `settings.corrupt.json` y se regeneran los valores por defecto.
- Los archivos de audio vivirán en `data/sounds/`; SQLite guarda solo metadatos y rutas.
- Datos y logs: `data/` (sobrescribible con la variable `XYRON_DATA_DIR`).

## Vista previa

`python scripts/render_preview.py preview.png` genera una captura offscreen de la ventana con datos de ejemplo.
