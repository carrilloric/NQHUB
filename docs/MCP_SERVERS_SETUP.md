# Guía de Instalación de Servidores MCP (Linear y Notion)

## 📋 ¿Qué es MCP?
Model Context Protocol (MCP) es un protocolo abierto creado por Anthropic que permite a los asistentes de IA conectarse de forma segura con herramientas y datos externos. Es como "USB-C para IA" - un conector universal.

## 🎯 Servidores Disponibles

### 1. Linear MCP Server
- **URL Oficial:** `https://mcp.linear.app/mcp`
- **Funciones:** Buscar, crear y actualizar issues, proyectos y comentarios
- **Mantenido por:** Linear (oficial)

### 2. Notion MCP Server
- **URL Oficial:** `https://mcp.notion.com/mcp`
- **NPM Package:** `@notionhq/notion-mcp-server`
- **Funciones:** Leer y escribir páginas, buscar contenido, gestionar tareas
- **Mantenido por:** Notion (oficial)

---

## 🚀 Instalación en Claude Desktop

### Paso 1: Localiza el archivo de configuración

El archivo se llama `claude_desktop_config.json` y está en:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### Paso 2: Obtén las credenciales

#### Para Linear:
1. Ve a `https://linear.app/TU-EQUIPO/settings/api`
2. Genera un nuevo Personal API Key
3. Copia el token (empieza con `lin_api_`)

#### Para Notion:
1. Ve a `https://www.notion.so/my-integrations`
2. Crea una nueva integración o usa una existente
3. Copia el Internal Integration Token (empieza con `secret_`)
4. **Importante:** Comparte las páginas que quieres acceder con tu integración:
   - En cada página de Notion, click en "..." → "Connections" → Agrega tu integración

### Paso 3: Configura los servidores

Edita el archivo `claude_desktop_config.json` y agrega:

```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"],
      "env": {
        "LINEAR_API_KEY": "lin_api_TU_TOKEN_AQUI"
      }
    },
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "NOTION_API_KEY": "secret_TU_TOKEN_AQUI"
      }
    }
  }
}
```

### Paso 4: Reinicia Claude Desktop

1. Cierra completamente Claude Desktop
2. Vuelve a abrirlo
3. Los servidores deberían estar disponibles

---

## 🔧 Configuración Alternativa (OAuth)

### Linear con OAuth (Más seguro)
Si prefieres OAuth en lugar de API key:
```json
{
  "linear": {
    "command": "npx",
    "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
    // No incluyas env, se autenticará con OAuth
  }
}
```

### Notion con OAuth
Para Notion, puedes usar el servidor remoto sin token:
```json
{
  "notion": {
    "command": "npx",
    "args": ["-y", "mcp-remote", "https://mcp.notion.com/mcp"]
    // Se autenticará vía OAuth cuando lo uses
  }
}
```

---

## ✅ Verificación

Para verificar que todo funciona:

1. Abre una nueva conversación en Claude Desktop
2. Pregunta:
   - "¿Puedes ver mis issues de Linear?"
   - "¿Puedes acceder a mis páginas de Notion?"
3. Si todo está bien configurado, podré:
   - **Linear:** Buscar, crear y actualizar issues
   - **Notion:** Leer y escribir en tus páginas compartidas

---

## 🛠️ Solución de Problemas Comunes

### Error: "No se puede conectar al servidor MCP"

**Causa común:** Node.js no está instalado
```bash
# Verifica si tienes Node.js
node --version

# Si no lo tienes, instálalo desde nodejs.org
```

### Error: "Permiso denegado" en Notion

**Solución:** Asegúrate de compartir las páginas con tu integración:
1. En Notion, abre la página que quieres acceder
2. Click en "..." (arriba a la derecha)
3. "Connections" → "Add connections"
4. Busca y agrega tu integración

### El servidor no aparece disponible

1. **Verifica el JSON:** Usa un validador JSON online para asegurar que no hay errores de sintaxis
2. **Revisa los logs:**
   - Mac: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### Error con NPX

Si `npx` no funciona, instala los paquetes globalmente:
```bash
# Para Linear
npm install -g mcp-remote

# Para Notion
npm install -g @notionhq/notion-mcp-server
```

Luego usa `mcp-remote` en lugar de `npx -y mcp-remote` en la configuración.

---

## 📝 Configuración Completa de Ejemplo

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
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "NOTION_API_KEY": "secret_abc123xyz789"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    }
  }
}
```

---

## 🔐 Seguridad

- **No compartas tus tokens:** Son como contraseñas
- **No subas el archivo de config a Git:** Agrega `claude_desktop_config.json` a `.gitignore`
- **Permisos limitados:** En Notion, solo comparte las páginas necesarias
- **Tokens seguros:** Guarda los tokens en un gestor de contraseñas

---

## 📚 Recursos Adicionales

- [Linear MCP Docs](https://linear.app/docs/mcp)
- [Notion MCP Docs](https://developers.notion.com/docs/mcp)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Servers Directory](https://mcpservers.org)

---

## 🎉 Funcionalidades Disponibles

### Con Linear puedo:
- Buscar issues por título, estado, asignado
- Crear nuevos issues con descripción completa
- Actualizar estado y propiedades de issues
- Agregar comentarios
- Gestionar proyectos

### Con Notion puedo:
- Leer el contenido de páginas
- Crear nuevas páginas y bases de datos
- Actualizar contenido existente
- Buscar en todo tu workspace
- Generar documentación automáticamente

---

*Última actualización: Marzo 2025*