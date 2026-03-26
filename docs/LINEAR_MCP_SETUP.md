# Guía de Instalación del Servidor MCP de Linear

## 📋 Resumen
Linear ofrece un servidor MCP oficial que permite a Claude acceder a tus issues, proyectos y comentarios de Linear de forma segura.

## 🎯 Opciones de Instalación

### Opción 1: Servidor Oficial de Linear (RECOMENDADO)
Linear mantiene un servidor MCP centralizado y gestionado.

**URL del servidor:** `https://mcp.linear.app/mcp`

### Opción 2: Servidor Comunitario (Deprecado)
Existe un servidor comunitario pero ya no se mantiene. Se recomienda usar el oficial.

## 🚀 Instalación Paso a Paso

### Para Claude Desktop (Windows/Mac)

#### Método A: Configuración Manual

1. **Obtén tu API Key de Linear:**
   - Ve a: `https://linear.app/TU-EQUIPO/settings/api`
   - Crea un nuevo API key personal
   - Copia el token generado

2. **Localiza el archivo de configuración de Claude:**
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

3. **Edita el archivo de configuración:**
   Agrega esta configuración al archivo JSON:

```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"],
      "env": {
        "LINEAR_API_KEY": "lin_api_TU_TOKEN_AQUI"
      }
    }
  }
}
```

#### Método B: Usando el Conector Integrado (Si está disponible)
1. En Claude Desktop, ve a: **Settings → Connectors**
2. Busca "Linear" y agrégalo
3. Autentícate cuando se te solicite

### Para Claude Code (Terminal)

Si estás usando Claude Code en la terminal:

```bash
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

Luego en tu sesión de Claude Code, ejecuta `/mcp` para autenticarte.

## 🔐 Configuración de Autenticación

### Usando API Key (Más Simple)
1. Genera un API key en Linear Settings
2. Agrégalo a la configuración como variable de entorno `LINEAR_API_KEY`

### Usando OAuth (Más Seguro)
El servidor soporta OAuth 2.1 con registro dinámico de cliente. Esto se configura automáticamente si usas el método del conector integrado.

## ✅ Verificación

Después de configurar:

1. **Reinicia Claude Desktop** completamente
2. En una nueva conversación, pregúntame: "¿Puedes ver mis issues de Linear?"
3. Debería poder acceder a:
   - Buscar issues
   - Crear nuevos issues
   - Actualizar issues existentes
   - Gestionar proyectos y comentarios

## 🛠️ Solución de Problemas

### Error: "No se puede conectar al servidor MCP"
- Verifica que tu API key sea válido
- Asegúrate de tener Node.js instalado (`node --version`)
- Verifica que la ruta del archivo de configuración sea correcta

### Error: "Permiso denegado"
- Verifica que tu API key tenga los permisos necesarios en Linear
- Algunos equipos requieren permisos específicos para acceso API

### El servidor no aparece disponible
1. Reinicia Claude Desktop completamente
2. Verifica que el JSON esté bien formateado (sin comas extras, comillas correctas)
3. Revisa los logs en: `~/Library/Logs/Claude/` (Mac) o `%APPDATA%\Claude\logs\` (Windows)

## 📝 Ejemplo de Configuración Completa

```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"],
      "env": {
        "LINEAR_API_KEY": "lin_api_abc123xyz789"
      }
    },
    "notion": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.notion.com/mcp"],
      "env": {
        "NOTION_TOKEN": "secret_abc123"
      }
    }
  }
}
```

## 🔗 Recursos Adicionales

- [Documentación oficial de Linear MCP](https://linear.app/docs/mcp)
- [Linear API Settings](https://linear.app/settings/api)
- [Model Context Protocol Docs](https://modelcontextprotocol.io)

## ⚠️ Notas Importantes

- Tu API key es sensible. No lo compartas ni lo subas a repositorios públicos
- El servidor MCP oficial de Linear es mantenido y actualizado regularmente
- Las funcionalidades pueden expandirse con el tiempo

---

*Última actualización: Marzo 2025*