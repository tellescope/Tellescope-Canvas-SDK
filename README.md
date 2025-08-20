Tellescope
=================

An Open-Source plugin for connecting the Canvas SDK to Tellescope

# Deployment

## Installing to Canvas
To deploy this plugin to your Canvas instance, please clone this repository. Please follow steps 1 and 2 of the official Canvas deployment guide: [Your First Plugin](http://docs.canvasmedical.com/guides/your-first-plugin/) to configure your own development environment. You should only need to do that once. 

## Configuring Protocols (Important!)

Before deploying to Canvas, you must configure which protocols to include in your plugin by running the interactive configuration script:

```bash
python3 configure_manifest.py
```

This script will:
- Scan the `protocols/` directory for available protocol files
- Display each protocol with its description
- Allow you to interactively select which protocols to include
- Generate the `CANVAS_MANIFEST.json` file with your selected protocols

The generated `CANVAS_MANIFEST.json` is used when installing this plugin to your Canvas instance. Only the protocols you select will be deployed and active in your Canvas environment.

### More Documentation

Other documentation can be found in the ./docs folder. These docs are primarily designed for consumption by AI coding assistants/agents and may read more as prompts than human-centered instructions. That said, they are worth reviewing before contributing to the code base. Please start at ./docs/contributing.md 
