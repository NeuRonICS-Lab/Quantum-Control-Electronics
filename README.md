# Quantum Control Electronics

## Overview
This project is a Quantum Control Electronics system designed to manage and control quantum hardware components. It includes Python scripts, configuration files, and hardware overlays for ADC and DAC operations.

## Folder Structure

### Python Scripts
Contains Python modules for ADC and DAC operations, utility functions, and main configuration scripts.

- **config.py**: Configuration settings for the project.
- **dac_Classes.py**: Classes for managing DAC operations, including waveform generation and configuration.
- **main.py**: Main entry point for the project.
- **mainConfig.py**: Configuration script for the main application.
- **readout_adc_classes.py**: Classes for managing ADC readout, including DMA and data streaming.
- **Utility_functions.py**: Utility functions used across the project.

### Ver1
Contains the first version of the project, including Jupyter notebooks and configuration scripts.

- **freq_sweep_checkout.ipynb**: Jupyter notebook for frequency sweep experiments.
- **SQ_CARS/**: Subfolder containing configuration and utility scripts for the first version.
  - **adcConfig.py**: ADC configuration settings.
  - **config.py**: General configuration settings.
  - **dacConfig.py**: DAC configuration settings.
  - **rfdcConfig.py**: RFDC configuration settings.
  - **utility_classes.py**: Utility classes for the first version.

### Ver2
Contains the second version of the project, including updated Jupyter notebooks and output files.

- **integrated_test.ipynb**: Jupyter notebook for integrated system testing.
- **output.log**: Log file for system outputs.
- **wave.txt**: Text file containing waveform data.
- **bitstreams/**: Subfolder containing hardware bitstream files.
  - **design_1_wrapper_jun18.bit**: Bitstream file for hardware configuration.
  - **design_1_wrapper_jun18.hwh**: Hardware wrapper file.
  - **design_1_wrapper_jun18.ltx**: Debug file for hardware.
- **SQ_CARS/**: Subfolder containing configuration and utility scripts for the second version.
  - **adcConfig.py**: ADC configuration settings.
  - **config.py**: General configuration settings.
  - **dacConfig.py**: DAC configuration settings.
  - **output.log**: Log file for the second version.
  - **rfdcConfig.py**: RFDC configuration settings.
  - **utility_classes.py**: Utility classes for the second version.

### Vivado Overlay Outputs
Contains hardware overlay files for the project.

- **design_1_wrapper.bit**: Bitstream file for hardware configuration.
- **design_1_wrapper.hwh**: Hardware wrapper file.
- **design_1.hwh**: Additional hardware wrapper file.

### doc
Contains project documentation.

- **documentation.txt**: Detailed documentation of the project.
- **project_diagram.dot**: Graphviz file representing the connectivity of modules.

### Root Files
- **four_qubit_rebuild.tcl**: TCL script for rebuilding the four-qubit system.
- **README.md**: This file, providing an overview of the project.

## How to Use
1. **Setup**: Ensure all dependencies are installed and the hardware is properly connected.
2. **Run Scripts**: Use `main.py` as the entry point to execute the project.
3. **Documentation**: Refer to the `doc` folder for detailed documentation and the block diagram.

## Block Diagram
The project includes a Graphviz file (`project_diagram.dot`) in the `doc` folder. Use Graphviz to render the file and visualize the connectivity of modules.

Reference link to rebuild project - https://github.com/jhallen/vivado_setup
