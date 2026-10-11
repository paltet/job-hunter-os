# Job Hunter OS

Herramienta local para organizar mi búsqueda de empleo: ofertas, candidaturas,
historial de estados y seguimientos en un solo sitio.

Construida con PostgreSQL, Python y Streamlit, y orquestada con Docker Compose.
Sin servicios de pago y sin automatizar cuentas de terceros.

## Funcionalidades actuales

- Registro de candidaturas con empresa, puesto, enlace, fuente y modalidad
- Pipeline de estados: saved, applied, interview, offer, rejected, withdrawn
- Historial de cada cambio de estado, para calcular estadísticas

## Cómo ejecutarlo

Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env     # y cambia la contraseña de POSTGRES_PASSWORD
docker compose up -d --build
```

Abre http://localhost:8501.

## Estructura

- `db/init/`: esquema SQL, que se carga en el primer arranque
- `app/`: panel en Streamlit
- `docker-compose.yml`: base de datos y aplicación

## Hoja de ruta

- [ ] Estadísticas en el panel
- [ ] Avisos y resumen diario por Telegram con n8n
- [ ] Detección de correos de procesos de selección
- [ ] Recordatorios de seguimiento

## Privacidad

Los datos viven solo en tu equipo. El archivo `.env` está en `.gitignore`
y nunca se sube al repositorio.