Tellescope
=================

An Open-Source plugin for connecting the Canvas SDK to Tellescope

# Deployment

## Quick Start - Deployment Shortcuts

### Deploy with Interactive Protocol Selection (Recommended)
```bash
python3 canvas_deploy.py install .
```

This command will:
- Run the interactive configuration script to let you choose specific protocols
- Install the plugin to your Canvas instance after configuration
- **Recommended for regular use** - ensures you only install protocols you actually need

### Deploy with All Protocols (Recommended for Developers/Contributors)
```bash
python3 canvas_deploy.py install . --all
```

This command will:
- Automatically configure the manifest with all available protocols
- Install the plugin to your Canvas instance
- No user interaction required
- **Recommended for development/testing** - installs the full scope of integration for comprehensive testing

### Deploy with Existing Configuration
```bash
python3 canvas_deploy.py install . --use-existing-configuration
```

This command will:
- Use the existing `CANVAS_MANIFEST.json` file (if it exists)
- Skip the configuration step entirely
- Install the plugin directly to your Canvas instance

## Manual Setup (Alternative)

### Installing to Canvas
To deploy this plugin manually to your Canvas instance, please clone this repository. Please follow steps 1 and 2 of the official Canvas deployment guide: [Your First Plugin](http://docs.canvasmedical.com/guides/your-first-plugin/) to configure your own development environment. You should only need to do that once. 

### Configuring Protocols (Important!)

Before deploying to Canvas manually, you must configure which protocols to include in your plugin by running the configuration script:

#### Interactive Configuration
```bash
python3 configure_manifest.py
```

#### Auto-select All Protocols
```bash
python3 configure_manifest.py --all
```

The configuration script will:
- Scan the `protocols/` directory for available protocol files
- Display each protocol with its description
- Allow you to interactively select which protocols to include (or auto-select all with `--all`)
- Generate the `CANVAS_MANIFEST.json` file with your selected protocols

The generated `CANVAS_MANIFEST.json` is used when installing this plugin to your Canvas instance. Only the protocols you select will be deployed and active in your Canvas environment.

#### Manual Canvas Installation
After configuring your manifest, install the plugin:
```bash
canvas install .
```

### More Documentation

Other documentation can be found in the ./docs folder. These docs are primarily designed for consumption by AI coding assistants/agents and may read more as prompts than human-centered instructions. That said, they are worth reviewing before contributing to the code base. Please start at ./docs/contributing.md 
