#!/bin/sh
set -eu

cd /app
lock_hash=$(sha256sum package-lock.json | cut -d ' ' -f1)
installed_hash_file=node_modules/.eventeveryday-lock-hash

if [ ! -f "$installed_hash_file" ] ||
   [ "$(cat "$installed_hash_file")" != "$lock_hash" ] ||
   ! npm ls --depth=0 >/dev/null 2>&1; then
    echo "Refreshing frontend dependencies from package-lock.json..."
    npm ci
    printf '%s\n' "$lock_hash" > "$installed_hash_file"
fi

exec npm run dev
