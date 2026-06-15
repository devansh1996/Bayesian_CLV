#!/usr/bin/env bash
# Compile thesis_clv.tex and write a versioned PDF (thesis_vN.pdf).
# Each run bumps to the next unused version number; pass -v N to force one.
set -euo pipefail
cd "$(dirname "$0")"

SRC="thesis_clv"
FORCE_V=""
[[ "${1:-}" == "-v" && -n "${2:-}" ]] && FORCE_V="$2"

latexmk -pdf -synctex=1 -interaction=nonstopmode -file-line-error "$SRC.tex"

if [[ -n "$FORCE_V" ]]; then
  N="$FORCE_V"
else
  N=1
  while [[ -e "thesis_v${N}.pdf" ]]; do N=$((N+1)); done
fi

cp "$SRC.pdf" "thesis_v${N}.pdf"
echo "✓ Wrote thesis_v${N}.pdf ($(pdfinfo "thesis_v${N}.pdf" 2>/dev/null | awk '/Pages/{print $2" pages"}'))"
