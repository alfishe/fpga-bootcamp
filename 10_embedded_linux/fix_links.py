import os
import glob
import re

base_dir = r'c:\Projects\Knowledge\fpga\10_embedded_linux'
subdirs = ['01_architecture','02_boot_flow','03_hps_fpga_bridges','04_drivers_and_dma','05_build_systems']

file_map = {
    'soc_linux_architecture.md': '01_architecture/soc_linux_architecture.md',
    'boot_flow.md': '02_boot_flow/boot_flow.md',
    'boot_flow_intel_soc.md': '02_boot_flow/boot_flow_intel_soc.md',
    'boot_flow_xilinx_zynq.md': '02_boot_flow/boot_flow_xilinx_zynq.md',
    'boot_flow_microchip_soc.md': '02_boot_flow/boot_flow_microchip_soc.md',
    'uboot.md': '02_boot_flow/uboot.md',
    'hps_fpga_bridges.md': '03_hps_fpga_bridges/hps_fpga_bridges.md',
    'hps_fpga_bridges_intel_soc.md': '03_hps_fpga_bridges/hps_fpga_bridges_intel_soc.md',
    'hps_fpga_bridges_xilinx_zynq.md': '03_hps_fpga_bridges/hps_fpga_bridges_xilinx_zynq.md',
    'hps_fpga_bridges_microchip_soc.md': '03_hps_fpga_bridges/hps_fpga_bridges_microchip_soc.md',
    'device_tree_and_overlays.md': '04_drivers_and_dma/device_tree_and_overlays.md',
    'kernel_drivers_and_dma.md': '04_drivers_and_dma/kernel_drivers_and_dma.md',
    'build_and_update.md': '05_build_systems/build_and_update.md'
}

def fix_links_in_file(filepath, current_subdir):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('[← Section Home](README.md)', '[← Section Home](../README.md)')
    content = content.replace('[← Project Home](../README.md)', '[← Project Home](../../README.md)')

    for old_name, new_path in file_map.items():
        pattern = r'\(' + re.escape(old_name) + r'\)'
        new_dir = new_path.split('/')[0]
        if current_subdir == new_dir:
            replacement = '(' + old_name + ')'
        else:
            replacement = '(../' + new_path + ')'
        content = re.sub(pattern, replacement, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for subdir in subdirs:
    dir_path = os.path.join(base_dir, subdir)
    for filepath in glob.glob(os.path.join(dir_path, '*.md')):
        fix_links_in_file(filepath, subdir)

print('Links fixed.')
