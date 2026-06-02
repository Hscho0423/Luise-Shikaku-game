# -*- coding: utf-8 -*-
"""
Luisegame 모바일 패치 스크립트
================================
저장소 루트(또는 이 스크립트가 있는 폴더)에서 실행:

  python fetch_and_patch_apple_game.py

동작:
  1) GitHub에서 apple_game.html 원본(raw)을 내려받습니다.
  2) iOS Safari / 홈 화면 추가에 맞는 meta·CSS·JS(동적 타일 크기 등)를 반영합니다.
  3) 드래그 합 말풍선 제거, 종료 오버레이에 「닫기」버튼(오버레이만 닫고 보드 정지 표시)을 반영합니다.
  4) 같은 폴더에 apple_game.html 로 저장합니다. 기존 파일은 apple_game.html.bak 으로 백업합니다.

인터넷 연결이 필요합니다. Python 3.8+ 권장.
"""
from __future__ import annotations

import re
import shutil
import sys
import urllib.request
from pathlib import Path

RAW_URL = "https://raw.githubusercontent.com/Hscho0423/Luisegame/main/apple_game.html"
INDEX_URL = "https://raw.githubusercontent.com/Hscho0423/Luisegame/main/index.html"

HEAD_INJECT = """
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="theme-color" content="#bcdcff" />
""".strip()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Luisegame-fetch-and-patch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def inject_head(html: str) -> str:
    if "viewport-fit=cover" in html:
        return html
    if re.search(r"<meta\s+charset", html, re.I):
        return re.sub(
            r"(<meta\s+charset=[^>]+>)",
            r"\1\n" + HEAD_INJECT,
            html,
            count=1,
            flags=re.I,
        )
    return re.sub(r"(<head[^>]*>)", r"\1\n" + HEAD_INJECT + "\n", html, count=1, flags=re.I)


def patch_css(html: str) -> str:
    html = re.sub(
        r"min-height:\s*100vh",
        "min-height: 100dvh;\n  min-height: -webkit-fill-available",
        html,
        count=1,
    )
    if "overscroll-behavior" not in html:
        html = re.sub(
            r"(body\s*\{)",
            r"\1\n  overscroll-behavior: none;\n  touch-action: manipulation;\n  -webkit-text-size-adjust: 100%;",
            html,
            count=1,
        )
    if "safe-area-inset" not in html:
        html = re.sub(
            r"(#layout\s*\{)",
            r"\1\n  padding-left: max(10px, env(safe-area-inset-left));\n  padding-right: max(10px, env(safe-area-inset-right));\n  padding-bottom: max(10px, env(safe-area-inset-bottom));",
            html,
            count=1,
        )
    html = re.sub(
        r"#settings\s*\{[^}]*font-size:\s*0\.5rem",
        lambda m: m.group(0).replace("font-size: 0.5rem", "font-size: clamp(0.72rem, 2.8vw, 0.95rem)"),
        html,
        count=1,
    )
    html = re.sub(
        r"(#settings h2\s*\{[^}]*font-size:\s*)0\.5rem",
        r"\g<1>clamp(0.72rem, 2.6vw, 0.9rem)",
        html,
        count=1,
    )
    html = re.sub(
        r"(\.field label\s*\{[^}]*font-size:\s*)0\.5rem",
        r"\g<1>clamp(0.72rem, 2.6vw, 0.9rem)",
        html,
        count=1,
    )
    html = re.sub(
        r"(\.field input\s*\{)",
        r"\1\n  min-height: 44px;\n  box-sizing: border-box;",
        html,
        count=1,
    )
    html = re.sub(
        r"(#apply-btn\s*\{)",
        r"\1\n  min-height: 44px;\n  min-width: 44px;",
        html,
        count=1,
    )
    if "#remain-btn {" not in html:
        needle = "#restart-btn:active { transform: scale(0.98); }"
        if needle in html:
            html = html.replace(
                needle,
                needle
                + """

#remain-btn {
  margin-top: 10px;
  font: inherit;
  font-size: 1rem;
  font-weight: 600;
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  background: #e8f4ff;
  color: #1a1a1a;
  cursor: pointer;
}
#remain-btn:hover { filter: brightness(1.02); }
@media (max-width: 520px) {
  #overlay-box { width: min(360px, calc(100vw - 28px)); padding: 22px 18px; }
  #restart-btn, #remain-btn, #overlay-close-btn { width: 100%; margin-left: 0; }
}
""",
            )
    return html


def patch_ui_drag_close(html: str) -> str:
    """말풍선 합 표시 제거, 종료 창 닫기 버튼 및 view-frozen 보드 표시."""
    if "// 말풍선: 선택 타일 바깥에만 배치" in html:
        html = re.sub(
            r"// 합 계산 \(빈칸은 0\)[\s\S]*?ctx\.save\(\);",
            "ctx.save();",
            html,
            count=1,
        )
        html = re.sub(
            r"\s*// 말풍선: 선택 타일 바깥에만 배치[\s\S]*?ctx\.fillText\(text,\s*bx\s*\+\s*bw\s*/\s*2,\s*by\s*\+\s*bh\s*/\s*2\s*\+\s*0\.5\);\s*",
            "\n        ",
            html,
            count=1,
        )
        html = html.replace(
            "// 드래그 중: 실제 터치 시작점부터 범위 표시 + 합 말풍선(항상 바깥)",
            "// 드래그 중: 선택 영역 표시",
        )

    if "canvas.view-finished" not in html:
        html = html.replace(
            "canvas.ended { pointer-events: none; cursor: default; opacity: 0.85; }",
            "canvas.ended { pointer-events: none; cursor: default; opacity: 0.85; }\n    canvas.view-finished { pointer-events: none; cursor: default; }",
            1,
        )

    if "#overlay-close-btn {" not in html:
        needle = "#remain-btn:hover { filter: brightness(1.02); }"
        if needle in html:
            html = html.replace(
                needle,
                needle
                + """

#overlay-close-btn {
  margin-top: 10px;
  font: inherit;
  font-size: 1rem;
  font-weight: 600;
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  background: #dfe6ee;
  color: #1a1a1a;
  cursor: pointer;
}
#overlay-close-btn:hover { filter: brightness(1.02); }
""",
                1,
            )

    html = html.replace(
        "#restart-btn, #remain-btn { width: 100%; margin-left: 0; }",
        "#restart-btn, #remain-btn, #overlay-close-btn { width: 100%; margin-left: 0; }",
    )

    if 'id="overlay-close-btn"' not in html:
        m = re.search(r'(<button[^>]+id="remain-btn"[^>]*>.*?</button>)', html, flags=re.I | re.DOTALL)
        if m:
            html = html.replace(m.group(1), m.group(1) + '\n<button type="button" id="overlay-close-btn">닫기</button>', 1)
        else:
            html = html.replace(
                '<button type="button" id="restart-btn">다시 하기</button>',
                '<button type="button" id="restart-btn">다시 하기</button>\n<button type="button" id="overlay-close-btn">닫기</button>',
                1,
            )

    if "overlayCloseBtn" not in html:
        html = html.replace(
            'const remainBtn = document.getElementById("remain-btn");',
            'const remainBtn = document.getElementById("remain-btn");\n'
            '    const overlayCloseBtn = document.getElementById("overlay-close-btn");',
            1,
        )

    marker = 'restartBtn.addEventListener("click", () => startNewGame());'
    close_block = """
    if (overlayCloseBtn) {
      overlayCloseBtn.addEventListener("click", () => {
        overlay.classList.remove("show");
        overlay.setAttribute("aria-hidden", "true");
        canvas.classList.remove("ended");
        canvas.classList.add("view-finished");
        draw();
      });
    }
"""
    if marker in html and "overlayCloseBtn.addEventListener" not in html:
        html = html.replace(marker, marker + close_block, 1)

    html = re.sub(
        r'(function startNewGame\(\) \{[\s\S]*?canvas\.classList\.remove\("ended"\);)\s*\n(?!\s*canvas\.classList\.remove\("view-finished"\))',
        r'\1\n      canvas.classList.remove("view-finished");\n',
        html,
        count=1,
    )

    old_r = 'canvas.classList.remove("ended"); // 미리보기 중 클릭/확인 가능'
    new_r = old_r + '\n      canvas.classList.remove("view-finished");'
    if old_r in html and new_r not in html:
        html = html.replace(old_r, new_r, 1)

    return html


def patch_js(html: str) -> str:
    if "function refreshCellSize" not in html:
        html = re.sub(r"\bconst\s+CELL\s*=\s*28\s*;", "let CELL = 28;", html, count=1)
        html = re.sub(
            r"let\s+GAME_SECONDS\s*=\s*120\s*;",
            """let GAME_SECONDS = 120;

function getFontPx() {
  return Math.max(11, Math.round(CELL * 0.56));
}

function refreshCellSize() {
  const vv = window.visualViewport;
  const iw = Math.min(
    vv && vv.width ? vv.width : 1e9,
    window.innerWidth || 1024,
    document.documentElement.clientWidth || 1024
  );
  const ih = Math.min(
    vv && vv.height ? vv.height : 1e9,
    window.innerHeight || 800
  );
  const maxBoardCssW = Math.min(520, iw * 0.96) - 8;
  const cellFromW = Math.floor((maxBoardCssW - PAD * 2) / COLS);
  const reserved = Math.min(260, Math.max(180, ih * 0.38));
  const maxBoardCssH = Math.max(140, ih - reserved);
  const cellFromH = Math.floor((maxBoardCssH - PAD * 2) / ROWS);
  CELL = Math.max(22, Math.min(40, Math.min(cellFromW, cellFromH)));
}

function onViewportResize() {
  resizeCanvas();
  draw();
}
""",
            html,
            count=1,
        )
        html = re.sub(
            r"const\s+fontPx\s*=\s*Math\.max\s*\(\s*11\s*,\s*Math\.round\s*\(\s*CELL\s*\*\s*0\.56\s*\)\s*\)\s*;",
            "",
            html,
            count=1,
        )
        html = html.replace(
            'ctx.font = "600 " + fontPx + "px Segoe UI, system-ui, sans-serif";',
            'ctx.font = "600 " + getFontPx() + "px Segoe UI, system-ui, sans-serif";',
        )
        html = re.sub(
            r"function\s+resizeCanvas\s*\(\s*\)\s*\{\s*canvas\.width",
            "function resizeCanvas() {\n  refreshCellSize();\n  canvas.width",
            html,
            count=1,
        )
        marker = 'canvas.addEventListener("pointerdown", onPointerDown);'
        if marker in html and "addEventListener(\"resize\", onViewportResize)" not in html:
            html = html.replace(
                marker,
                'window.addEventListener("resize", onViewportResize);\n'
                "if (window.visualViewport) {\n"
                '  window.visualViewport.addEventListener("resize", onViewportResize);\n'
                "}\n"
                + marker,
                1,
            )
    return html


def patch_index(html: str) -> str:
    if "viewport-fit=cover" in html:
        return html
    if re.search(r"<meta\s+charset", html, re.I):
        block = (
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />\n'
            '<meta name="theme-color" content="#bcdcff" />\n'
        )
        return re.sub(r"(<meta\s+charset=[^>]+>)", r"\1\n" + block, html, count=1, flags=re.I)
    return re.sub(
        r"(<head[^>]*>)",
        r'\1\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />\n'
        r'<meta name="theme-color" content="#bcdcff" />\n',
        html,
        count=1,
        flags=re.I,
    )


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    apple_path = out_dir / "apple_game.html"
    index_path = out_dir / "index.html"

    try:
        raw = fetch(RAW_URL)
    except Exception as e:
        print("다운로드 실패:", e, file=sys.stderr)
        return 1

    if "<html" not in raw.lower() and "<!doctype" not in raw.lower():
        print("예상과 다른 응답(HTML이 아님). URL을 확인하세요.", file=sys.stderr)
        return 1

    patched = patch_ui_drag_close(patch_js(patch_css(inject_head(raw))))

    if apple_path.is_file():
        shutil.copyfile(apple_path, out_dir / "apple_game.html.bak")

    apple_path.write_text(patched, encoding="utf-8", newline="\n")
    print("저장:", apple_path, "bytes", len(patched.encode("utf-8")))

    try:
        idx = fetch(INDEX_URL)
        idx2 = patch_index(idx)
        if index_path.is_file():
            shutil.copyfile(index_path, out_dir / "index.html.bak")
        index_path.write_text(idx2, encoding="utf-8", newline="\n")
        print("저장:", index_path)
    except Exception as e:
        print("index.html 패치 생략:", e, file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
