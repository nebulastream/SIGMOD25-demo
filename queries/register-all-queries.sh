#!/usr/bin/bash
set -eu
shopt -s nullglob

NES_HOST="${NES_HOST:-nes:8080}"
QUERY_DIR="${QUERY_DIR:-/queries}"
EXTRA_FLAGS="${EXTRA_FLAGS:--x}"

host="${NES_HOST%%:*}"
port="${NES_HOST##*:}"

if [ "$#" -gt 0 ]; then
  files="$*"
else
  set -- "$QUERY_DIR"/*.yml "$QUERY_DIR"/*.yaml
  files="$*"
fi

ls $QUERY_DIR

[ -e "$(printf '%s\n' $files | head -n1)" ] || {
  echo "No query files found in $QUERY_DIR" >&2
  exit 1
}

for f in $files; do
  [ -f "$f" ] || continue
  echo "Registering $(basename "$f")"
  nes-nebuli register -s "$NES_HOST" $EXTRA_FLAGS -i "$f"
done

echo "All queries registered!"

#while [ "$(nes-nebuli status -s nes:8080 $QUERY_ID)" == "Running" ]; do
#    sleep 1
#done