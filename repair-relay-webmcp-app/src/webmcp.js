export async function registerWebMCPTools(tools, onStatus = () => {}) {
  const modelContext = document.modelContext;
  if (!modelContext || typeof modelContext.registerTool !== "function") {
    onStatus({
      supported: false,
      registered: 0,
      message: "WebMCP unavailable — use ChatGPT’s in-app browser or enable Chrome WebMCP testing."
    });
    return { supported: false, registered: 0, errors: [] };
  }

  const errors = [];
  let registered = 0;

  for (const tool of tools) {
    try {
      await document.modelContext.registerTool(tool);
      registered += 1;
    } catch (error) {
      errors.push({ name: tool.name, message: error instanceof Error ? error.message : String(error) });
    }
  }

  const supported = registered === tools.length;
  onStatus({
    supported,
    registered,
    message: supported
      ? `WebMCP ready · ${registered} tools`
      : `WebMCP partial · ${registered}/${tools.length} tools`
  });

  return { supported, registered, errors };
}
