import os
import subprocess
import json
from fastmcp import FastMCP, resources

# Create a basic server instance
mcp = FastMCP(name="MyIndigoMCPServer")

# You can also add instructions for how to interact with the server
mcp_with_instructions = FastMCP(
    name="IndigoAssistant",
    instructions="""
        This server provides an interface to the Indigo Home Automation Server.
    """,
)

# Indigo Script Runner
def indigo_run_script(script) -> str:
    result = subprocess.run(
        ["indigo-host", "-e", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise RuntimeError(f"Indigo error: {result.stderr}")

# Indigo-Specific Functions
def indigo_get_folders() -> list:
    indigo_code = """
import json
folders = []
for folder in indigo.devices.folders:
    folders.append(dict(folder))
return (json.dumps(folders, indent=4, cls=indigo.utils.IndigoJSONEncoder))
"""
    return indigo_run_script(indigo_code)

def indigo_get_device(deviceId) -> list:
    indigo_code = f"""
import json
devices = []
for device in indigo.devices:
    if device.id == {deviceId}:
        devices.append(dict(device))
return (json.dumps(devices, indent=4, cls=indigo.utils.IndigoJSONEncoder))
"""
    return indigo_run_script(indigo_code)

def indigo_get_devices(folderId) -> list:
    indigo_code = f"""
import json
devices = []
for device in indigo.devices:
    if device.folderId == {folderId}:
        devices.append({{
            "device_id": device.id,
            "device_name": device.name
        }})
return (json.dumps(devices, indent=4, cls=indigo.utils.IndigoJSONEncoder))
"""
    return indigo_run_script(indigo_code)

def indigo_turn_device_on_or_off(device_id: int, state: str) -> str:
    indigo_code = f"""
import json
if "{state}" == "on":
    indigo.device.turnOn({device_id})
else:
    indigo.device.turnOff({device_id})
return (json.dumps(dict(indigo.devices[{device_id}]), indent=4, cls=indigo.utils.IndigoJSONEncoder))
"""
    return indigo_run_script(indigo_code)

def indigo_set_device_brightness(device_id: int, brightness: int, delay: int = 0) -> str:
    indigo_code = f"""
import json
indigo.dimmer.setBrightness({device_id}, value={brightness}, delay={delay})
return (json.dumps(dict(indigo.devices[{device_id}]), indent=4, cls=indigo.utils.IndigoJSONEncoder))
"""
    return indigo_run_script(indigo_code)

def indigo_get_logs(date: str) -> resources:
    url = f"/Library/Application Support/Perceptive Automation/Indigo 2024.2/Logs/{date} Events.log"
    return ResourceReference(
        name="indigo_log_file",
        description=f"Indigo log file for {date}",
        url=url
    )

# MCP Tools

@mcp.tool
def list_folders(params, context):
    """Returns the folders in Indigo."""
    folders = indigo_get_folders()
    json_text = json.dumps(folders, indent=2)
    return json_text
        
@mcp.tool
def list_devices(params, context):
    """Returns a list of all devices in a given folder."""
    if isinstance(params, str):
        params = json.loads(params)
        
    folder_id = params["folder_id"]
    return indigo_get_devices(folder_id)
        
@mcp.tool
def get_device(params, context):
    """Gets information about a device."""
    if isinstance(params, str):
        params = json.loads(params)
        
    device_id = params["device_id"]
    return indigo_get_device(device_id)
        
@mcp.tool
def turn_device_on_or_off(params, context):
    """Turns a device on or off."""
    if isinstance(params, str):
        params = json.loads(params)
        
    device_id = params["device_id"]
    state = params["state"]
    result = indigo_turn_device_on_or_off(device_id, state)
    return result
    
@mcp.tool
def set_device_brightness(params, context):
    """Sets a device's brightness (assuming it has a brightness characteristic)."""
    if isinstance(params, str):
        params = json.loads(params)
        
    device_id = params["device_id"]
    brightness = params["brightness"]
    delay = params["delay"]
    result = indigo_set_device_brightness(device_id, brightness, delay)
    return result
    
@mcp.tool
def get_logs(params, context) -> str:
    """Returns the log file for a given date in the format YYYY-MM-DD."""
    date = params["date"]
    # Return a resource reference
    resource = indigo_get_logs(date)
    return resource

@mcp.prompt
def analyze_data(data_points: list[float]) -> str:
    """Creates a prompt asking for analysis of numerical data."""
    formatted_data = ", ".join(str(point) for point in data_points)
    return f"Please analyze these data points: {formatted_data}"        
    
if __name__ == "__main__":
    # This runs the server, defaulting to STDIO transport
    mcp.run()
  
