# Configuración de MCP para Claude Code (CLI)

## 🚀 Instalación Rápida

Claude Code usa comandos simples para agregar servidores MCP. No necesitas editar archivos JSON manualmente.

## 📋 Linear

### Paso 1: Obtén tu API Key
Ve a `https://linear.app/TU-EQUIPO/settings/api` y genera un Personal API Key.

### Paso 2: Agrega el servidor
```bash
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

### Paso 3: Configura el token
Cuando ejecutes `/mcp` en Claude Code, te pedirá autenticación. Puedes:
- Usar OAuth (más fácil)
- O configurar tu API key como variable de entorno:
```bash
export LINEAR_API_KEY="lin_api_TU_TOKEN_AQUI"
```

## 📝 Notion

### Paso 1: Obtén tu Integration Token
1. Ve a `https://www.notion.so/my-integrations`
2. Crea una nueva integración
3. Copia el Internal Integration Token (empieza con `secret_`)

### Paso 2: Agrega el servidor
```bash
claude mcp add notion https://mcp.notion.com/mcp
```

O si prefieres el servidor NPM local:
```bash
claude mcp add notion @notionhq/notion-mcp-server
```

### Paso 3: Configura el token
```bash
export NOTION_API_KEY="secret_TU_TOKEN_AQUI"
```

### Paso 4: Comparte páginas con tu integración
En Notion, para cada página que quieras acceder:
- Click en "..." → "Connections" → Agrega tu integración

## ✅ Verificación

En tu sesión de Claude Code:

```bash
# Lista los servidores MCP disponibles
/mcp list

# Autentícate si es necesario
/mcp auth

# Prueba Linear
# Pregúntame: "¿Puedes ver mis issues de Linear?"

# Prueba Notion
# Pregúntame: "¿Puedes acceder a mis páginas de Notion?"
```

## 🔧 Configuración con Variables de Entorno

Si prefieres configurar todo de una vez, agrega a tu `.bashrc` o `.zshrc`:

```bash
# Linear
export LINEAR_API_KEY="lin_api_TU_TOKEN"

# Notion
export NOTION_API_KEY="secret_TU_TOKEN"
```

Luego recarga tu shell:
```bash
source ~/.bashrc  # o source ~/.zshrc
```

## 🛠️ Comandos Útiles de Claude Code

```bash
# Ver todos los servidores MCP instalados
claude mcp list

# Remover un servidor
claude mcp remove linear-server

# Ver información de un servidor
claude mcp info linear-server

# Actualizar servidores
claude mcp update
```

## 📦 Instalación Alternativa (NPM directo)

Si prefieres instalar los paquetes globalmente:

```bash
# Instalar paquetes
npm install -g mcp-remote
npm install -g @notionhq/notion-mcp-server

# Agregar a Claude Code
claude mcp add linear mcp-remote https://mcp.linear.app/mcp
claude mcp add notion @notionhq/notion-mcp-server
```

## 🔐 Seguridad

- **No hardcodees tokens:** Usa variables de entorno
- **Usa `.env` files:** Para proyectos específicos
- **Agrega a `.gitignore`:** Nunca subas tokens a Git

### Ejemplo con archivo `.env`:
```bash
# Crea un archivo .env en tu proyecto
echo 'LINEAR_API_KEY="lin_api_xxx"' >> .env
echo 'NOTION_API_KEY="secret_xxx"' >> .env

# Carga las variables antes de usar Claude Code
source .env
claude
```

## ❓ Troubleshooting

### "Command not found: claude"
Asegúrate de tener Claude Code instalado:
```bash
npm install -g @anthropic-ai/claude-cli
```

### "MCP server not responding"
```bash
# Verifica que Node.js esté instalado
node --version

# Reinstala el servidor
claude mcp remove linear-server
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

### "Authentication failed"
- Verifica que tu token sea válido
- Para Linear: El token debe empezar con `lin_api_`
- Para Notion: El token debe empezar con `secret_`

## 🎉 Listo!

Una vez configurado, en cualquier sesión de Claude Code puedo:
- 📋 Buscar y crear issues en Linear
- 📝 Leer y escribir en Notion
- 🔄 Sincronizar información entre ambas plataformas
- 🤖 Automatizar flujos de trabajo

---

*Última actualización: Marzo 2025*