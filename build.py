"""
Build script — สร้าง SmartTextToSpeech.exe
รันด้วย: python build.py
"""
import subprocess
import sys
import shutil
from pathlib import Path
from PIL import Image, ImageDraw


BASE = Path(__file__).parent


def create_icon():
    """สร้าง icon.ico สำหรับ exe."""
    sizes = [16, 32,48, 64, 128, 256]
    frames = []
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        m = size // 32          # scale factor
        # Purple circle
        d.ellipse([m, m, size-m, size-m], fill=(124, 58, 237, 255))
        # Mic body
        cx = size // 2
        bw = max(4, size // 5)
        d.rounded_rectangle(
            [cx-bw, size//6, cx+bw, size//2],
            radius=max(2, size//8), fill=(255, 255, 255, 255)
        )
        # Mic stand
        sw = max(1, size // 20)
        d.rectangle([cx-sw, size//2, cx+sw, size*3//4], fill=(255, 255, 255, 255))
        # Base
        d.arc(
            [cx - size//5, size*2//3, cx + size//5, size*5//6],
            start=180, end=0,
            fill=(255, 255, 255, 255),
            width=max(1, size // 24),
        )
        frames.append(img)

    icon_path = BASE / 'icon.ico'
    frames[0].save(
        icon_path, format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f'  icon.ico created ({icon_path})')
    return icon_path


def clean():
    for folder in ['build', 'dist']:
        p = BASE / folder
        if p.exists():
            shutil.rmtree(p)
            print(f'  Removed {folder}/')
    spec_build = BASE / '__pycache__'
    if spec_build.exists():
        shutil.rmtree(spec_build)


def build():
    print('\n' + '='*52)
    print('  SmartTextToSpeech — Build')
    print('='*52)

    print('\n[1/3] Creating icon...')
    create_icon()

    print('\n[2/3] Cleaning previous build...')
    clean()

    print('\n[3/3] Running PyInstaller...')
    result = subprocess.run(
        [sys.executable, '-m', 'PyInstaller', 'build.spec', '--clean', '--noconfirm'],
        cwd=str(BASE),
    )

    if result.returncode != 0:
        print('\nBuild FAILED.')
        sys.exit(1)

    output = BASE / 'dist' / 'SmartTextToSpeech'
    exe    = output / 'SmartTextToSpeech.exe'

    print('\n' + '='*52)
    if exe.exists():
        size_mb = sum(f.stat().st_size for f in output.rglob('*') if f.is_file()) / 1_048_576
        print(f'  Build SUCCESS!')
        print(f'  Output folder : dist/SmartTextToSpeech/')
        print(f'  Exe           : SmartTextToSpeech.exe')
        print(f'  Total size    : {size_mb:.1f} MB')
        print(f'\n  Double-click SmartTextToSpeech.exe to run')
        print(f'  Share the entire dist/SmartTextToSpeech/ folder')
    else:
        print('  Build finished but exe not found — ตรวจสอบ error ด้านบน')
    print('='*52 + '\n')


if __name__ == '__main__':
    build()
